import time, re, json, requests, random, string
from urllib.parse import unquote, quote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

VIDEO_URL = 'https://www.tiktok.com/@guarddiszen1/video/7645679725960056095'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'

def get_play_count():
    s = requests.Session()
    r = s.get(VIDEO_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15)
    pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>'
    uni_match = re.search(pattern, r.text, re.DOTALL)
    if uni_match:
        decoded = unquote(uni_match.group(1))
        data = json.loads(decoded)
        stats = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {}).get('stats', {})
        return stats.get('playCount', 0)
    return -1

def make_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    options.add_argument("--disable-cookies")
    options.add_argument("--incognito")
    
    ua_variant = UA.replace('Chrome/125.0.0.0', f'Chrome/{random.randint(120,130)}.0.0.0')
    options.add_argument(f"user-agent={ua_variant}")
    
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = {runtime: {}};
        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
        """
    })
    
    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
        "headers": {
            "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        }
    })
    
    return driver

before = get_play_count()
print(f'Before: {before}')

print('\n--- Test: Incognito + cookieless + X-Forwarded-For spoof ---')
for i in range(5):
    driver = None
    try:
        driver = make_driver()
        driver.get(VIDEO_URL)
        try:
            WebDriverWait(driver, 12).until(EC.presence_of_element_located((By.TAG_NAME, "video")))
        except:
            pass
        
        vids = driver.find_elements(By.TAG_NAME, "video")
        if vids:
            driver.execute_script("arguments[0].muted=true;arguments[0].play();", vids[0])
        
        time.sleep(8)
    except Exception as e:
        print(f'  Run {i+1} error: {str(e)[:80]}')
    finally:
        if driver:
            try: driver.quit()
            except: pass
    
    mid = get_play_count()
    print(f'  Run {i+1}: playCount={mid} (diff: {mid - before})')

after1 = get_play_count()
print(f'\nAfter incognito test: {after1} (diff: {after1 - before})')

if after1 == before:
    print('\n--- Test: CDP network intercept to simulate different IPs ---')
    print('Spoofing different IP addresses via X-Forwarded-For and proxy headers')
    
    for i in range(3):
        driver = None
        try:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--window-size=1920,1080")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            driver = webdriver.Chrome(options=options)
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            })
            
            fake_ip = f"{random.randint(1,223)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            
            driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
                "headers": {
                    "X-Forwarded-For": fake_ip,
                    "X-Real-IP": fake_ip,
                    "X-Client-IP": fake_ip,
                    "CF-Connecting-IP": fake_ip,
                    "True-Client-IP": fake_ip,
                }
            })
            
            driver.get(VIDEO_URL)
            try:
                WebDriverWait(driver, 12).until(EC.presence_of_element_located((By.TAG_NAME, "video")))
            except:
                pass
            
            vids = driver.find_elements(By.TAG_NAME, "video")
            if vids:
                driver.execute_script("arguments[0].muted=true;arguments[0].play();", vids[0])
            
            time.sleep(8)
            print(f'  Spoofed IP {fake_ip}: playCount={get_play_count()}')
        except Exception as e:
            print(f'  Error: {str(e)[:80]}')
        finally:
            if driver:
                try: driver.quit()
                except: pass

after2 = get_play_count()
print(f'\nFinal: {after2} (total diff: {after2 - before})')

if after2 == before:
    print('\n--- Checking if TikTok even counts headless browser views ---')
    print('TikTok may require real GPU rendering + audio context for view counting')
    print('The video_play Tea event IS being sent (status 200) but TikTok server-side may reject it')
    print('based on bot fingerprinting (missing WebGL, audio fingerprint, etc.)')
