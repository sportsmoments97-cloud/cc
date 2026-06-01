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
    
    print('Waiting 20s for video_play event...')
    time.sleep(20)
    
    logs = driver.get_log("performance")
    
    video_play_found = False
    for entry in logs:
        try:
            msg = json.loads(entry.get('message', '{}'))
            method = msg.get('message', {}).get('method', '')
            if method == 'Network.requestWillBeSent':
                params = msg.get('message', {}).get('params', {})
                request = params.get('request', {})
                url = request.get('url', '')
                post_data = request.get('postData', '')
                
                if 'mcs.tiktok' in url and 'list' in url and post_data and 'video_play' in post_data:
                    video_play_found = True
                    print(f'\n!!! FOUND video_play request !!!')
                    print(f'URL: {url}')
                    
                    try:
                        pd = json.loads(post_data)
                        if isinstance(pd, list):
                            for item in pd:
                                events = item.get('events', [])
                                for ev in events:
                                    if ev.get('event') == 'video_play':
                                        print(f'\nvideo_play event:')
                                        params_str = ev.get('params', '')
                                        if isinstance(params_str, str):
                                            try:
                                                p = json.loads(params_str)
                                                print(json.dumps(p, indent=2)[:800])
                                            except:
                                                print(params_str[:500])
                                        elif isinstance(params_str, dict):
                                            print(json.dumps(params_str, indent=2)[:800])
                                        
                                        print(f'\nFull event object (minus params):')
                                        ev_copy = {k: v for k, v in ev.items() if k != 'params'}
                                        print(json.dumps(ev_copy, indent=2)[:300])
                                
                                header = item.get('header', {})
                                if header:
                                    print(f'\nTea header:')
                                    print(json.dumps(header, indent=2)[:500])
                                    
                                user = item.get('user', {})
                                if user:
                                    print(f'\nTea user:')
                                    print(json.dumps(user, indent=2)[:200])
                    except Exception as e:
                        print(f'Parse error: {e}')
                        print(f'Raw postData: {post_data[:500]}')
        except:
            pass
    
    if not video_play_found:
        print('NO video_play event found in 20s!')
        print('\nAll events seen:')
        for entry in logs:
            try:
                msg = json.loads(entry.get('message', '{}'))
                method = msg.get('message', {}).get('method', '')
                if method == 'Network.requestWillBeSent':
                    request = msg.get('message', {}).get('params', {}).get('request', {})
                    url = request.get('url', '')
                    post_data = request.get('postData', '')
                    if 'mcs.tiktok' in url and 'list' in url and post_data:
                        try:
                            pd = json.loads(post_data)
                            if isinstance(pd, list):
                                for item in pd:
                                    for ev in item.get('events', []):
                                        event_name = ev.get('event', '')
                                        if 'video' in event_name.lower() or 'play' in event_name.lower() or 'vv' in event_name.lower():
                                            print(f'  EVENT: {event_name}')
                        except:
                            pass
            except:
                pass

except Exception as e:
    print(f'Error: {e}')
finally:
    try:
        driver.quit()
    except:
        pass

after = get_play_count()
print(f'\nAfter: {after} (diff: {after - before})')
