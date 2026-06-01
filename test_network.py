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

def create_driver():
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
        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """
    })
    return driver

before = get_play_count()
print(f'Before: {before}')

print('\n--- Intercept network traffic during video play ---')
driver = None
try:
    driver = create_driver()
    driver.execute_cdp_cmd("Network.enable", {})
    
    requests_log = []
    def on_request(request):
        url = request.get('params', {}).get('request', {}).get('url', '')
        if any(k in url.lower() for k in ['report', 'event', 'tea', 'beacon', 'monitor', 'track', 'heartbeat', 'commit']):
            requests_log.append(url)
    
    driver.execute_cdp_cmd("Fetch.enable", {"patterns": [{"urlPattern": "*"}]})
    
    driver.get(VIDEO_URL)
    
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "video"))
        )
    except:
        pass
    
    video_elements = driver.find_elements(By.TAG_NAME, "video")
    if video_elements:
        driver.execute_script("arguments[0].play();", video_elements[0])
    
    time.sleep(15)
    
    print('\nNetwork requests to tracking/reporting URLs:')
    for url in requests_log[:20]:
        print(f'  {url[:120]}')
    
    print(f'\nTotal tracking requests: {len(requests_log)}')
    
    logs = driver.get_log("performance")
    print('\nPerformance log entries with report/event/tea:')
    for entry in logs:
        msg = entry.get('message', '')
        if any(k in msg.lower() for k in ['report', 'event', 'tea', 'beacon', 'mcs.', 'monitor']):
            print(f'  {msg[:150]}')

except Exception as e:
    print(f'Error: {e}')
finally:
    if driver:
        try:
            driver.quit()
        except:
            pass

after = get_play_count()
print(f'\nAfter: {after} (diff: {after - before})')
