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

print('Monitoring play count every 10s for 2 minutes...')
print('(Watch the video in YOUR browser on your phone or different network)')
print(f'URL: {VIDEO_URL}')
print()

counts = set()
for i in range(12):
    c = get_play_count()
    counts.add(c)
    print(f'  {i*10}s: {c}')
    if i < 11:
        time.sleep(10)

if len(counts) == 1:
    print(f'\nCount stayed at {counts.pop()} the entire time.')
    print('This could mean:')
    print('1. Server-side cache (TikTok updates counts in batches, not real-time)')
    print('2. Same-IP deduplication')
    print('3. The SSR HTML is cached by CDN (not the real count)')
    
    print('\n--- Trying API endpoint for real-time count ---')
    video_id = '7645679725960056095'
    
    url = f'https://www.tiktok.com/api/item/detail/?itemId={video_id}'
    headers = {
        'User-Agent': UA,
        'Accept': 'application/json',
        'Referer': VIDEO_URL,
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f'API status: {r.status_code}, len: {len(r.text)}')
        if r.text:
            try:
                data = r.json()
                print(f'API response keys: {list(data.keys())[:10]}')
                print(f'API response: {json.dumps(data, indent=2)[:500]}')
            except:
                print(f'Not JSON: {r.text[:200]}')
    except Exception as e:
        print(f'API error: {e}')
else:
    print(f'\nCount changed! Values seen: {sorted(counts)}')
