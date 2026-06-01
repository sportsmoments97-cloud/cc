import time, re, json, requests
from urllib.parse import unquote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

VIDEO_ID = '7645679725960056095'
VIDEO_URL = f'https://www.tiktok.com/@guarddiszen1/video/{VIDEO_ID}'
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

print('\n--- Test: Load embed iframe in Chrome ---')
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--window-size=1280,720")
options.add_argument(f"user-agent={UA}")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
})

try:
    html = f"""
    <html><body style="margin:0;background:#000">
    <h1 style="color:white;text-align:center;padding:20px">Loading TikTok...</h1>
    <blockquote class="tiktok-embed" cite="{VIDEO_URL}" data-video-id="{VIDEO_ID}" style="max-width:605px;min-width:325px;">
        <section><a target="_blank" title="@guarddiszen1" href="{VIDEO_URL}">@guarddiszen1</a></section>
    </blockquote>
    <script async src="https://www.tiktok.com/embed.js"></script>
    </body></html>
    """
    
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html)
        tmp_path = f.name
    
    driver.get(f'file:///{tmp_path}')
    print('Embed page loaded, waiting 25s...')
    time.sleep(25)
    
    os.unlink(tmp_path)
except Exception as e:
    print(f'Error: {e}')
finally:
    try: driver.quit()
    except: pass

after1 = get_play_count()
print(f'After embed: {after1} (diff: {after1 - before})')

print('\n--- Test: Direct embed URL visit ---')
options2 = Options()
options2.add_argument("--headless=new")
options2.add_argument("--disable-gpu")
options2.add_argument("--no-sandbox")
options2.add_argument("--disable-dev-shm-usage")
options2.add_argument("--disable-blink-features=AutomationControlled")
options2.add_argument("--window-size=1280,720")
options2.add_argument(f"user-agent={UA}")
options2.add_experimental_option("excludeSwitches", ["enable-automation"])
options2.add_experimental_option("useAutomationExtension", False)

driver2 = webdriver.Chrome(options=options2)
driver2.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
})

try:
    embed_url = f'https://www.tiktok.com/embed/v2/{VIDEO_ID}'
    driver2.get(embed_url)
    print('Embed v2 page loaded, waiting 25s...')
    time.sleep(25)
except Exception as e:
    print(f'Error: {e}')
finally:
    try: driver2.quit()
    except: pass

after2 = get_play_count()
print(f'After embed v2 visit: {after2} (diff: {after2 - before})')

print('\n--- Test: Multiple page loads in same session (refresh) ---')
options3 = Options()
options3.add_argument("--headless=new")
options3.add_argument("--disable-gpu")
options3.add_argument("--no-sandbox")
options3.add_argument("--disable-dev-shm-usage")
options3.add_argument("--disable-blink-features=AutomationControlled")
options3.add_argument("--window-size=1280,720")
options3.add_argument(f"user-agent={UA}")
options3.add_experimental_option("excludeSwitches", ["enable-automation"])
options3.add_experimental_option("useAutomationExtension", False)

driver3 = webdriver.Chrome(options=options3)
driver3.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
})

try:
    for i in range(10):
        driver3.get(VIDEO_URL)
        try:
            WebDriverWait(driver3, 8).until(EC.presence_of_element_located((By.TAG_NAME, "video")))
        except:
            pass
        vids = driver3.find_elements(By.TAG_NAME, "video")
        if vids:
            driver3.execute_script("arguments[0].muted=true;arguments[0].play();", vids[0])
        time.sleep(5)
        mid = get_play_count()
        print(f'  Refresh {i+1}: playCount={mid} (diff: {mid - before})')
except Exception as e:
    print(f'Error: {e}')
finally:
    try: driver3.quit()
    except: pass

final = get_play_count()
print(f'\nFinal: {final} (total diff: {final - before})')
