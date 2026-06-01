import time, re, json, requests
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

def get_play_count_from_js(driver):
    try:
        return driver.execute_script("""
            var el = document.querySelector('[data-e2e="browse-video-count"]');
            if (el) return el.textContent;
            var strongs = document.querySelectorAll('strong');
            for (var s of strongs) {
                var text = s.textContent;
                if (text.includes('Views') || text.includes('views') || text.match(/\\d+K/)) {
                    return text;
                }
            }
            return null;
        """)
    except:
        return None

before = get_play_count()
print(f'Before: {before}')

print('\n--- Test: Visible Chrome, read count FROM the page itself ---')
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
    
    print('Page loaded. Looking for view count element...')
    
    page_html_snippet = driver.execute_script("""
        var body = document.body.innerHTML;
        var idx = body.indexOf('playCount');
        if (idx > -1) return body.substring(Math.max(0, idx - 50), idx + 100);
        idx = body.indexOf('Views');
        if (idx > -1) return body.substring(Math.max(0, idx - 100), idx + 50);
        return 'not found';
    """)
    print(f'Page HTML snippet: {page_html_snippet[:200]}')
    
    view_count_text = get_play_count_from_js(driver)
    print(f'View count from page element: {view_count_text}')
    
    all_text = driver.execute_script("""
        var result = [];
        var elems = document.querySelectorAll('[data-e2e]');
        for (var e of elems) {
            if (e.dataset.e2e.includes('count') || e.dataset.e2e.includes('view') || e.dataset.e2e.includes('like') || e.dataset.e2e.includes('stat')) {
                result.push(e.dataset.e2e + ': ' + e.textContent);
            }
        }
        return result.join(' | ');
    """)
    print(f'Data-e2e elements: {all_text}')
    
    print('\nFull page text search for numbers near "views":')
    count_info = driver.execute_script("""
        var text = document.body.innerText;
        var lines = text.split('\\n');
        var result = [];
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            if (line.match(/\\d/) && (line.toLowerCase().includes('view') || line.toLowerCase().includes('play') || line.toLowerCase().includes('watch'))) {
                result.push(line.substring(0, 100));
            }
        }
        return result.join(' | ');
    """)
    print(f'Count info: {count_info}')
    
    print('\nAll strong/h3/h4 elements with numbers:')
    numbered_elements = driver.execute_script("""
        var result = [];
        var elems = document.querySelectorAll('h3, h4, strong, span[data-e2e]');
        for (var e of elems) {
            var text = e.textContent.trim();
            if (text.match(/^\\d/) && text.length < 30) {
                result.push(e.tagName + '[' + (e.dataset.e2e || '') + ']: ' + text);
            }
        }
        return result.join(' | ');
    """)
    print(f'Numbered elements: {numbered_elements}')
    
    print('\n--- Playing video, then checking after 30s ---')
    vids = driver.find_elements(By.TAG_NAME, "video")
    if vids:
        driver.execute_script("arguments[0].muted=true;arguments[0].play();", vids[0])
    
    time.sleep(30)
    
    page_count = get_play_count_from_js(driver)
    server_count = get_play_count()
    print(f'Page shows: {page_count}, Server SSR says: {server_count}')
    
    print('\nChecking performance logs for video_play responses...')
    logs = driver.get_log("performance")
    for entry in logs:
        try:
            msg = json.loads(entry.get('message', '{}'))
            method = msg.get('message', {}).get('method', '')
            if method == 'Network.responseReceived':
                params = msg.get('message', {}).get('params', {})
                response = params.get('response', {})
                url = response.get('url', '')
                if 'mcs.tiktok' in url and 'list' in url:
                    status = response.get('status', 0)
                    print(f'  Tea response: {url[:60]}... status={status}')
        except:
            pass

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    try: driver.quit()
    except: pass
