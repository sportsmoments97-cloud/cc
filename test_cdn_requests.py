import time, re, json, requests, random
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

print('\n--- Capturing ALL network requests during a real page visit ---')
print('Looking specifically for video CDN stream URLs and heartbeat/ping endpoints')

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
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
})

try:
    driver.get(VIDEO_URL)
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "video")))
    except:
        pass
    
    vids = driver.find_elements(By.TAG_NAME, "video")
    if vids:
        driver.execute_script("arguments[0].muted=true;arguments[0].play();", vids[0])
    
    time.sleep(20)
    
    logs = driver.get_log("performance")
    
    cdn_urls = []
    heartbeat_urls = []
    report_urls = []
    all_video_related = []
    
    for entry in logs:
        try:
            msg = json.loads(entry.get('message', '{}'))
            method = msg.get('message', {}).get('method', '')
            
            if method == 'Network.requestWillBeSent':
                params = msg.get('message', {}).get('params', {})
                request = params.get('request', {})
                url = request.get('url', '')
                post_data = request.get('postData', '')
                
                if any(x in url for x in ['tiktokcdn', 'tiktokv.com', 'ibytedtos', 'bytecdn', 'byteimg']):
                    cdn_urls.append(url[:150])
                
                if any(x in url.lower() for x in ['heartbeat', 'report', 'ping', 'track', 'count', 'view', 'play', 'beacon', 'commit']):
                    is_api = '/api/' in url
                    heartbeat_urls.append({
                        'url': url[:200],
                        'method': request.get('method', ''),
                        'post': post_data[:200] if post_data else '',
                        'is_api': is_api,
                    })
                
                if any(x in url for x in ['video', 'aweme', 'item/detail', 'item/report']):
                    all_video_related.append(url[:200])
                    
        except:
            pass
    
    print(f'\n=== CDN URLs ({len(cdn_urls)}) ===')
    seen = set()
    for u in cdn_urls:
        short = u.split('?')[0]
        if short not in seen:
            seen.add(short)
            print(f'  {u}')
    
    print(f'\n=== Heartbeat/Report/Ping URLs ({len(heartbeat_urls)}) ===')
    seen2 = set()
    for h in heartbeat_urls:
        key = h['url'].split('?')[0]
        if key not in seen2:
            seen2.add(key)
            print(f'  [{h["method"]}] {h["url"]}')
            if h['post']:
                print(f'    POST data: {h["post"][:150]}')
    
    print(f'\n=== Video-related URLs ({len(all_video_related)}) ===')
    seen3 = set()
    for u in all_video_related:
        if u not in seen3:
            seen3.add(u)
            print(f'  {u}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    try: driver.quit()
    except: pass

after = get_play_count()
print(f'\nAfter: {after} (diff: {after - before})')
