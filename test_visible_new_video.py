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

before = get_play_count()
print(f'Before: {before}')

print('\n--- Test: Non-headless Chrome, real browser, click play ---')
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--window-size=1280,720")
options.add_argument(f"user-agent={UA}")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

driver = webdriver.Chrome(options=options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    window.chrome = {runtime: {}};
    """
})

try:
    driver.get(VIDEO_URL)
    
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "video")))
    except:
        pass
    
    print('Page loaded, checking video state...')
    vids = driver.find_elements(By.TAG_NAME, "video")
    if vids:
        paused = driver.execute_script("return arguments[0].paused;", vids[0])
        ready = driver.execute_script("return arguments[0].readyState;", vids[0])
        duration = driver.execute_script("return arguments[0].duration;", vids[0])
        src = driver.execute_script("return arguments[0].src || arguments[0].querySelector('source')?.src;", vids[0])
        print(f'  paused={paused}, readyState={ready}, duration={duration}')
        print(f'  src={str(src)[:100] if src else "None"}')
        
        driver.execute_script("""
            var v = arguments[0];
            v.muted = true;
            v.play().then(() => console.log('play() succeeded')).catch(e => console.log('play() failed:', e));
        """, vids[0])
    
    print('Watching for 30s...')
    for i in range(6):
        time.sleep(5)
        mid = get_play_count()
        ct = driver.execute_script("return arguments[0].currentTime;", vids[0]) if vids else 0
        p = driver.execute_script("return arguments[0].paused;", vids[0]) if vids else True
        print(f'  {5*(i+1)}s: playCount={mid} (diff: {mid-before}), video currentTime={ct:.1f}, paused={p}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    try: driver.quit()
    except: pass

after = get_play_count()
print(f'\nAfter visible Chrome: {after} (diff: {after - before})')

if after == before:
    print('\n--- Still 0. Now please watch the video in YOUR real browser ---')
    print(f'Open: {VIDEO_URL}')
    print('Then run check_count.py')
