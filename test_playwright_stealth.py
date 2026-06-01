import time, re, json, requests, random
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

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

stealth = Stealth()

print('\n--- Test: Playwright with stealth (non-headless) ---')
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=['--disable-blink-features=AutomationControlled', '--enable-webgl']
    )
    context = browser.new_context(
        user_agent=UA,
        viewport={'width': 1280, 'height': 720},
        locale='en-US',
        timezone_id='America/New_York',
    )
    
    page = context.new_page()
    stealth.apply_stealth_sync(page)
    
    page.goto(VIDEO_URL, wait_until='domcontentloaded', timeout=30000)
    print('Page loaded with stealth')
    
    try:
        page.wait_for_selector('video', timeout=15000)
        print('Video element found')
    except:
        print('Video element not found')
    
    video = page.query_selector('video')
    if video:
        page.evaluate('(vid) => { vid.muted = true; vid.play(); }', video)
        print('Video play triggered')
    
    print('Watching for 30s...')
    time.sleep(30)
    
    mid = get_play_count()
    print(f'After 30s stealth watch: {mid} (diff: {mid - before})')
    
    browser.close()

after1 = get_play_count()
print(f'\nAfter stealth test: {after1} (diff: {after1 - before})')
