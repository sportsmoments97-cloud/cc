import time
import re
import json
import requests
from urllib.parse import unquote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

VIDEO_URL = 'https://www.tiktok.com/@guarddiszen/video/7645452587629661470'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'

def get_play_count():
    s = requests.Session()
    r = s.get(VIDEO_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15)
    uni_match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>', r.text, re.DOTALL)
    if uni_match:
        decoded = unquote(uni_match.group(1))
        data = json.loads(decoded)
        stats = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {}).get('stats', {})
        return stats.get('playCount', 0)
    return 0

before = get_play_count()
print(f'Before: {before}')

print('\n--- TEST: Non-headless Chrome (visible browser) ---')
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
    
    print('Page loaded, waiting 5s...')
    time.sleep(5)
    
    video_elements = driver.find_elements(By.TAG_NAME, "video")
    if video_elements:
        driver.execute_script("""
            var vid = arguments[0];
            vid.muted = true;
            vid.play();
        """, video_elements[0])
        print('Video play triggered')
    
    print('Watching video for 30s...')
    for i in range(6):
        time.sleep(5)
        mid = get_play_count()
        print(f'  {5*(i+1)}s: playCount={mid} (diff: {mid - before})')
    
    mid = get_play_count()
    print(f'\nAfter 30s visible watch: {mid} (diff: {mid - before})')
    
    if mid == before:
        print('\nStill no change. Checking if video actually played...')
        duration = driver.execute_script("return arguments[0].duration;", video_elements[0])
        current = driver.execute_script("return arguments[0].currentTime;", video_elements[0])
        paused = driver.execute_script("return arguments[0].paused;", video_elements[0])
        print(f'  Video duration: {duration}, currentTime: {current}, paused: {paused}')
        
        print('\nTrying click-to-play approach...')
        driver.execute_script("""
            var vid = arguments[0];
            vid.currentTime = 0;
            vid.muted = false;
        """, video_elements[0])
        time.sleep(1)
        
        actions = ActionChains(driver)
        actions.move_to_element(video_elements[0]).click().perform()
        time.sleep(3)
        
        current = driver.execute_script("return arguments[0].currentTime;", video_elements[0])
        paused = driver.execute_script("return arguments[0].paused;", video_elements[0])
        print(f'  After click: currentTime={current}, paused={paused}')
        
        time.sleep(15)
        final_check = get_play_count()
        print(f'  After click+15s: playCount={final_check} (diff: {final_check - before})')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    try:
        driver.quit()
    except:
        pass

after = get_play_count()
print(f'\nFinal: {after} (total diff: {after - before})')
