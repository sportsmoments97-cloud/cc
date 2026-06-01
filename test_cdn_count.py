import time, re, json, requests, random, threading
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

print('\n--- Test: Free proxy from webproxy.to or similar ---')
print('Trying to find working HTTPS proxies...')

proxy_list = [
    'https://api.allorigins.win/raw?url=' + requests.utils.quote(VIDEO_URL),
]

print('\n--- Test: Use a web fetch service to get the count from different IPs ---')
free_apis = [
    f'https://api.allorigins.win/raw?url={requests.utils.quote(VIDEO_URL)}',
    f'https://api.codetabs.com/v1/proxy?quest={VIDEO_URL}',
]

for api_url in free_apis:
    try:
        r = requests.get(api_url, timeout=20)
        pattern = r'"playCount":(\d+)'
        matches = re.findall(pattern, r.text)
        print(f'  {api_url[:50]}: playCounts={matches[:3]}, len={len(r.text)}')
    except Exception as e:
        print(f'  {api_url[:50]}: error={str(e)[:60]}')

print('\n--- Test: Mobile API endpoint ---')
video_id = '7645679725960056095'
mobile_url = f'https://api16-normal-useast5.us.tiktokv.com/aweme/v1/aweme/detail/?aweme_id={video_id}&aid=1988'
try:
    r = requests.get(mobile_url, headers={'User-Agent': 'com.zhiliaoapp.musically/2021600040 (Linux; U; Android 11; en_US; Pixel 4; Build/RQ3A.210805.001.A1; Cronet/58.0.2991.0)'}, timeout=10)
    print(f'Mobile API: status={r.status_code}, len={len(r.text)}')
    if r.text:
        try:
            data = r.json()
            aweme = data.get('aweme_detail', {})
            stats = aweme.get('statistics', {})
            print(f'Mobile stats: {json.dumps(stats, indent=2)[:300]}')
        except:
            print(f'Response: {r.text[:200]}')
except Exception as e:
    print(f'Mobile API error: {str(e)[:80]}')

print('\n--- Test: TikTok internal SSR with different cookie values ---')
for i in range(3):
    try:
        s = requests.Session()
        s.cookies.set('tt_webid', str(random.randint(1000000000000000000, 9999999999999999999)), domain='.tiktok.com')
        s.cookies.set('tt_webid_v2', str(random.randint(1000000000000000000, 9999999999999999999)), domain='.tiktok.com')
        s.cookies.set('msToken', ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_', k=128)), domain='.tiktok.com')
        r = s.get(VIDEO_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15)
        pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>'
        uni_match = re.search(pattern, r.text, re.DOTALL)
        if uni_match:
            decoded = unquote(uni_match.group(1))
            data = json.loads(decoded)
            stats = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {}).get('stats', {})
            print(f'  Random cookies {i+1}: playCount={stats.get("playCount", "?")}')
    except Exception as e:
        print(f'  Error: {str(e)[:60]}')

after = get_play_count()
print(f'\nCurrent count: {after} (diff: {after - before})')

print('\n=== CRITICAL INSIGHT ===')
print('The count stays at 7 regardless of browser type. Possible explanations:')
print('1. TikTok counts views server-side ONLY when the video data is fetched from CDN')
print('   (not from Tea events, not from page loads, but from actual video stream requests)')
print('2. The CDN request must include proper X-Bogus + a_bogus tokens')
print('3. TikTok deduplicates by IP - same IP never counts more than 1 view')
print('4. The SSR playCount is cached and updates every few hours')
print('\nLet me check if the video CDN stream request is what actually counts...')
