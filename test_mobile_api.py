import time, re, json, requests, random, hashlib
from urllib.parse import unquote

VIDEO_URL = 'https://www.tiktok.com/@guarddiszen1/video/7645679725960056095'
VIDEO_ID = '7645679725960056095'
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

print('\n=== Testing TikTok Mobile API ===')
print('The mobile app counts views differently than web - it uses video download/stream requests')

mobile_apis = [
    {
        'name': 'aweme/detail (v1)',
        'url': f'https://api16-normal-useast5.us.tiktokv.com/aweme/v1/aweme/detail/?aweme_id={VIDEO_ID}&aid=1988&app_name=musical_ly&version_code=300000&device_id={random.randint(1000000000000000000, 9999999999999999999)}',
        'headers': {
            'User-Agent': 'com.zhiliaoapp.musically/300000 (Linux; U; Android 12; en_US; Pixel 6; Build/SD1A.210817.036; Cronet/58.0.2991.0)',
        },
    },
    {
        'name': 'aweme/detail (v2 with more params)',
        'url': f'https://api16-normal-useast5.us.tiktokv.com/aweme/v1/aweme/detail/?aweme_id={VIDEO_ID}&aid=1988&app_name=musical_ly&version_code=300000&device_platform=android&device_type=Pixel+6&os_version=12&device_id={random.randint(1000000000000000000, 9999999999999999999)}&channel=googleplay',
        'headers': {
            'User-Agent': 'com.zhiliaoapp.musically/300000 (Linux; U; Android 12; en_US; Pixel 6; Build/SD1A.210817.036; Cronet/58.0.2991.0)',
            'x-tt-token': '',
            'sdk-version': '2',
        },
    },
    {
        'name': 'aweme/aweme/detail (alternate path)',
        'url': f'https://api22-normal-useast5.us.tiktokv.com/aweme/v1/aweme/detail/?aweme_id={VIDEO_ID}&aid=1988&app_name=musical_ly&version_code=320000&device_id={random.randint(1000000000000000000, 9999999999999999999)}',
        'headers': {
            'User-Agent': 'com.zhiliaoapp.musically/320000 (Linux; U; Android 13; en_US; Pixel 7; Build/TQ2A.230305.008.C1; Cronet/58.0.2991.0)',
        },
    },
]

for api in mobile_apis:
    try:
        r = requests.get(api['url'], headers=api['headers'], timeout=10)
        print(f'\n{api["name"]}:')
        print(f'  Status: {r.status_code}, Length: {len(r.text)}')
        if r.text and len(r.text) > 10:
            try:
                data = r.json()
                aweme = data.get('aweme_detail', {})
                if aweme:
                    stats = aweme.get('statistics', {})
                    print(f'  Stats: {json.dumps(stats, indent=2)[:300]}')
                    video = aweme.get('video', {})
                    play_addr = video.get('play_addr', {})
                    if play_addr:
                        print(f'  Video play URLs: {len(play_addr.get("url_list", []))} URLs')
                        for u in play_addr.get('url_list', [])[:2]:
                            print(f'    {u[:100]}...')
                else:
                    print(f'  Response keys: {list(data.keys())[:10]}')
                    print(f'  Response: {json.dumps(data, indent=2)[:300]}')
            except:
                print(f'  Not JSON: {r.text[:200]}')
    except Exception as e:
        print(f'  Error: {str(e)[:80]}')

print('\n=== Testing: Hit video CDN directly (stream download) ===')
cdn_url = f'https://v16-webapp-prime.us.tiktok.com/video/tos/useast8/tos-useast8-ve-0068c003-tx2/oUfbIJrIjqJelKBopAAd0RdNgAzUzwGeAZYILC/?a=1988&bti=ODszNWYuMDE6&&bt=693&ft=4KJMyMzm8Zmo0~6vEa4jVnybdpWrKsd.&mime_type=video_mp4&qs=4&l=20260601003053A4BE94F5E1D10FE2B877&cv=live&cs=21718&ch=&cbr=&cd=0%3A0%3A0%3A0&chd=&cr=&cp=&cplat=web&cprv=&csc=&csz=0&cvs=3&e=&exp=&ftv=0&l=20260601003053A4BE94F5E1D10FE2B877&lv=20260601003053A4BE94F5E1D10FE2B877&mt=0&nt=&p=&pf=web&pt=0&rcm=&sc=&sft=&sk=&sl=&sn=&sp=&sr=&st=&sz=0&tp=&tt=&tz=America%2FNew_York&vd=&vf=&vl=&vn=&vpl='

try:
    r = requests.head(cdn_url, headers={'User-Agent': UA, 'Referer': 'https://www.tiktok.com/'}, timeout=10, allow_redirects=True)
    print(f'CDN HEAD: {r.status_code}, content-type: {r.headers.get("content-type", "?")}, content-length: {r.headers.get("content-length", "?")}')
except Exception as e:
    print(f'CDN error: {str(e)[:80]}')

print('\n=== Testing: Send view report via mobile heartbeat API ===')
for i in range(5):
    device_id = str(random.randint(1000000000000000000, 9999999999999999999))
    try:
        url = f'https://api16-normal-useast5.us.tiktokv.com/aweme/v1/aweme/report/?aweme_id={VIDEO_ID}&aid=1988&app_name=musical_ly&version_code=300000&device_platform=android&device_id={device_id}'
        r = requests.post(url, headers={
            'User-Agent': 'com.zhiliaoapp.musically/300000 (Linux; U; Android 12; en_US; Pixel 6; Build/SD1A.210817.036)',
            'Content-Type': 'application/x-www-form-urlencoded',
        }, data=f'aweme_id={VIDEO_ID}&play_type=0', timeout=10)
        print(f'  Report {i+1}: status={r.status_code}, body={r.text[:100] if r.text else "empty"}')
    except Exception as e:
        print(f'  Report {i+1}: error={str(e)[:60]}')

mid = get_play_count()
print(f'\nMid-check: {mid} (diff: {mid - before})')

print('\n=== Testing: Video play count via /v1/aweme/stats ===')
for i in range(3):
    device_id = str(random.randint(1000000000000000000, 9999999999999999999))
    try:
        url = f'https://api16-normal-useast5.us.tiktokv.com/aweme/v1/aweme/stats/?aweme_id={VIDEO_ID}&aid=1988&app_name=musical_ly&version_code=300000&device_platform=android&device_id={device_id}'
        r = requests.get(url, headers={
            'User-Agent': 'com.zhiliaoapp.musically/300000 (Linux; U; Android 12; en_US; Pixel 6)',
        }, timeout=10)
        print(f'  Stats {i+1}: status={r.status_code}, body={r.text[:200] if r.text else "empty"}')
    except Exception as e:
        print(f'  Stats {i+1}: error={str(e)[:60]}')

after = get_play_count()
print(f'\nAfter: {after} (diff: {after - before})')
