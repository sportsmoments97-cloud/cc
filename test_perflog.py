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
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "video")))
    except:
        pass
    
    video_elements = driver.find_elements(By.TAG_NAME, "video")
    if video_elements:
        driver.execute_script("arguments[0].play();", video_elements[0])
    
    time.sleep(10)
    
    logs = driver.get_log("performance")
    tracking_urls = []
    for entry in logs:
        try:
            msg = json.loads(entry.get('message', '{}'))
            method = msg.get('message', {}).get('method', '')
            if method == 'Network.requestWillBeSent':
                url = msg.get('message', {}).get('params', {}).get('request', {}).get('url', '')
                if any(k in url.lower() for k in ['report', 'event', 'tea', 'beacon', 'mcs', 'monitor', 'track', 'heartbeat', 'commit', 'list/']):
                    tracking_urls.append(url)
        except:
            pass
    
    print(f'\nFound {len(tracking_urls)} tracking/report URLs:')
    for url in tracking_urls[:30]:
        print(f'  {url[:150]}')

except Exception as e:
    print(f'Error: {e}')
finally:
    try:
        driver.quit()
    except:
        pass

after = get_play_count()
print(f'\nAfter: {after} (diff: {after - before})')
