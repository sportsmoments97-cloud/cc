import time, re, json, requests
from urllib.parse import unquote

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

print(f'Before: {get_play_count()}')

print('\n--- Using public proxy list to test different IP ---')
proxies_to_test = [
    'http://81.17.192.79:80',
    'http://51.79.50.22:9300',
    'http://64.225.8.192:80',
    'http://185.162.231.19:80',
    'http://45.76.29.109:8080',
]

for proxy in proxies_to_test:
    try:
        s = requests.Session()
        s.proxies = {'http': proxy, 'https': proxy}
        r = s.get(VIDEO_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15)
        pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>'
        uni_match = re.search(pattern, r.text, re.DOTALL)
        if uni_match:
            decoded = unquote(uni_match.group(1))
            data = json.loads(decoded)
            stats = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {}).get('stats', {})
            print(f'  Proxy {proxy}: playCount={stats.get("playCount", "?")}, status={r.status_code}')
        else:
            print(f'  Proxy {proxy}: status={r.status_code}, no data (len={len(r.text)})')
    except Exception as e:
        print(f'  Proxy {proxy}: {str(e)[:80]}')

print(f'\nAfter: {get_play_count()}')
