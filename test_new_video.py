import time, re, json, requests
from urllib.parse import unquote
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
    options.add_argument(f"user-agent={UA}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = {runtime: {}};
        """
    })
    return driver

before = get_play_count()
print(f'Before: {before}')

print('\n--- Test 1: Single Chrome session, watch 20s ---')
driver = None
try:
    driver = make_driver()
    driver.get(VIDEO_URL)
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "video")))
    except:
        pass
    
    vids = driver.find_elements(By.TAG_NAME, "video")
    if vids:
        driver.execute_script("""
            var v = arguments[0];
            v.muted = true;
            v.play();
        """, vids[0])
        print('Video play triggered')
    
    time.sleep(20)
except Exception as e:
    print(f'Error: {e}')
finally:
    if driver:
        try: driver.quit()
        except: pass

after1 = get_play_count()
print(f'After 1 Chrome session (20s watch): {after1} (diff: {after1 - before})')

print('\n--- Test 2: 5 sequential Chrome sessions ---')
for i in range(5):
    driver = None
    try:
        driver = make_driver()
        driver.get(VIDEO_URL)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "video")))
        except:
            pass
        vids = driver.find_elements(By.TAG_NAME, "video")
        if vids:
            driver.execute_script("arguments[0].muted=true;arguments[0].play();", vids[0])
        time.sleep(8)
    except Exception as e:
        print(f'  Session {i+1} error: {e}')
    finally:
        if driver:
            try: driver.quit()
            except: pass
    
    mid = get_play_count()
    print(f'  After session {i+1}: {mid} (total diff: {mid - before})')

after2 = get_play_count()
print(f'\nFinal: {after2} (total diff: {after2 - before})')
