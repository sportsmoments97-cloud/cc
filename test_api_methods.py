import time, re, json, requests
from urllib.parse import unquote

VIDEO_URL = 'https://www.tiktok.com/@guarddiszen1/video/7645679725960056095'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'

def get_play_count_via_api():
    headers = {
        'User-Agent': UA,
        'Accept': 'application/json',
    }
    url = f'https://api.tiklytics.eu/v1/video/info?url={VIDEO_URL}'
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        print(f'Tiklytics: {json.dumps(data, indent=2)[:500]}')
        return
    except Exception as e:
        print(f'Tiklytics error: {e}')

def get_play_count_via_tiktok_api():
    video_id = '7645679725960056095'
    headers = {
        'User-Agent': UA,
        'Accept': 'application/json',
        'Referer': 'https://www.tiktok.com/',
    }
    
    url = f'https://www.tiktok.com/api/item/detail/?itemId={video_id}&aid=1988'
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f'API status: {r.status_code}')
        if r.status_code == 200:
            try:
                data = r.json()
                item = data.get('itemDetail', data.get('itemInfo', {}))
                stats = item.get('stats', {})
                print(f'API stats: {json.dumps(stats, indent=2)}')
            except:
                print(f'API response (raw): {r.text[:500]}')
        else:
            print(f'API response: {r.text[:300]}')
    except Exception as e:
        print(f'API error: {e}')

def check_embed():
    embed_url = f'https://www.tiktok.com/embed/v2/{7645679725960056095}'
    try:
        r = requests.get(embed_url, headers={'User-Agent': UA}, timeout=10)
        pattern = r'"playCount":(\d+)'
        matches = re.findall(pattern, r.text)
        print(f'Embed playCount values: {matches}')
    except Exception as e:
        print(f'Embed error: {e}')

def check_oembed():
    url = f'https://www.tiktok.com/oembed?url={VIDEO_URL}'
    try:
        r = requests.get(url, headers={'User-Agent': UA}, timeout=10)
        data = r.json()
        print(f'oEmbed: {json.dumps(data, indent=2)[:500]}')
    except Exception as e:
        print(f'oEmbed error: {e}')

print('=== Method 1: Tiklytics API ===')
get_play_count_via_api()

print('\n=== Method 2: TikTok item/detail API ===')
get_play_count_via_tiktok_api()

print('\n=== Method 3: Embed page ===')
check_embed()

print('\n=== Method 4: oEmbed ===')
check_oembed()

print('\n=== Method 5: SSR (our current method) ===')
s = requests.Session()
r = s.get(VIDEO_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15)
pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>'
uni_match = re.search(pattern, r.text, re.DOTALL)
if uni_match:
    decoded = unquote(uni_match.group(1))
    data = json.loads(decoded)
    stats = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {}).get('stats', {})
    print(f'SSR playCount: {stats.get("playCount", "N/A")}')
