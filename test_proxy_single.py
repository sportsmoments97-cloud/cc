import requests, re, json
from urllib.parse import unquote

VIDEO_URL = 'https://www.tiktok.com/@guarddiszen1/video/7645679725960056095'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'

def get_play_count_with_proxy(proxy_url):
    try:
        s = requests.Session()
        s.proxies = {'http': proxy_url, 'https': proxy_url}
        r = s.get(VIDEO_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=10)
        pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>'
        uni_match = re.search(pattern, r.text, re.DOTALL)
        if uni_match:
            decoded = unquote(uni_match.group(1))
            data = json.loads(decoded)
            stats = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {}).get('stats', {})
            return stats.get('playCount', '?'), r.status_code
        return 'no data', r.status_code
    except Exception as e:
        return str(e)[:60], 'err'

proxy = 'http://64.225.8.192:80'
print(f'Testing proxy: {proxy}')
count, status = get_play_count_with_proxy(proxy)
print(f'Result: playCount={count}, status={status}')

proxy2 = 'http://81.17.192.79:80'
print(f'\nTesting proxy: {proxy2}')
count2, status2 = get_play_count_with_proxy(proxy2)
print(f'Result: playCount={count2}, status={status2}')
