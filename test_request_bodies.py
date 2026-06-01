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
    
    time.sleep(15)
    
    logs = driver.get_log("performance")
    
    tea_requests = []
    webid_requests = []
    api_requests = []
    
    for entry in logs:
        try:
            msg = json.loads(entry.get('message', '{}'))
            method = msg.get('message', {}).get('method', '')
            
            if method == 'Network.requestWillBeSent':
                params = msg.get('message', {}).get('params', {})
                request = params.get('request', {})
                url = request.get('url', '')
                post_data = request.get('postData', '')
                request_headers = request.get('headers', {})
                
                if 'mcs.tiktokw.us/v1/list' in url or 'mcs.tiktokv.us/v1/list' in url:
                    tea_requests.append({
                        'url': url,
                        'postData': post_data[:500] if post_data else '',
                        'headers': {k: v for k, v in request_headers.items() if k.lower() in ['content-type', 'x-csrf-token', 'cookie']},
                    })
                elif 'webid' in url:
                    webid_requests.append({
                        'url': url,
                        'postData': post_data[:500] if post_data else '',
                    })
                elif '/api/' in url and 'tiktok.com' in url:
                    api_requests.append({
                        'url': url[:200],
                        'method': request.get('method', ''),
                        'postData': post_data[:300] if post_data else '',
                    })
        except:
            pass
    
    print(f'\n=== Tea SDK /v1/list requests ({len(tea_requests)}) ===')
    for i, req in enumerate(tea_requests[:5]):
        print(f'\n  Request {i+1}:')
        print(f'    URL: {req["url"]}')
        print(f'    Headers: {json.dumps(req["headers"], indent=2)[:200]}')
        if req['postData']:
            try:
                pd = json.loads(req['postData'])
                print(f'    PostData keys: {list(pd.keys())[:10]}')
                if 'events' in pd:
                    events = pd['events']
                    if isinstance(events, list):
                        for ev in events[:3]:
                            print(f'      event: {ev.get("event", "?")}')
                            params = ev.get('params', '')
                            if isinstance(params, str):
                                try:
                                    p = json.loads(params)
                                    print(f'        params: {json.dumps(p, indent=2)[:300]}')
                                except:
                                    print(f'        params (raw): {params[:200]}')
                            elif isinstance(params, dict):
                                print(f'        params: {json.dumps(params, indent=2)[:300]}')
                if 'header' in pd:
                    h = pd['header']
                    print(f'    Header: app_id={h.get("app_id","?")}, aid={h.get("aid","?")}, web_id={h.get("web_id","?")[:20]}')
            except:
                print(f'    PostData (raw): {req["postData"][:300]}')

    print(f'\n=== WebID requests ({len(webid_requests)}) ===')
    for i, req in enumerate(webid_requests[:3]):
        print(f'  {i+1}: {req["url"][:100]}')
        if req['postData']:
            print(f'     data: {req["postData"][:200]}')

    print(f'\n=== API requests ({len(api_requests)}) ===')
    for i, req in enumerate(api_requests[:5]):
        print(f'  {i+1}: {req["method"]} {req["url"]}')
        if req['postData']:
            print(f'     data: {req["postData"][:150]}')

except Exception as e:
    print(f'Error: {e}')
finally:
    try:
        driver.quit()
    except:
        pass

after = get_play_count()
print(f'\nAfter: {after} (diff: {after - before})')
