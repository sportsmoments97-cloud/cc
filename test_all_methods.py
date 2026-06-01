import requests
import re
import json
import time
from urllib.parse import unquote

VIDEO_SHORT_URL = 'https://www.tiktok.com/t/ZP8sJg5YR/'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'

def get_play_count(session=None):
    s = session or requests.Session()
    r = s.get(VIDEO_SHORT_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15, allow_redirects=True)
    uni_match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>', r.text, re.DOTALL)
    if uni_match:
        decoded = unquote(uni_match.group(1))
        data = json.loads(decoded)
        stats = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {}).get('stats', {})
        return stats.get('playCount', 0), r.url
    return 0, ''

count, resolved = get_play_count()
print(f'Current play count: {count}')
print(f'Resolved URL: {resolved}')

video_id = re.search(r'/video/(\d+)', resolved)
video_id = video_id.group(1) if video_id else 'unknown'
print(f'Video ID: {video_id}')

print('\n' + '='*60)
print('TESTING DIFFERENT VIEW REGISTRATION METHODS')
print('='*60)

def baseline_count():
    s = requests.Session()
    r = s.get(VIDEO_SHORT_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15, allow_redirects=True)
    uni_match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>', r.text, re.DOTALL)
    if uni_match:
        decoded = unquote(uni_match.group(1))
        data = json.loads(decoded)
        stats = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {}).get('stats', {})
        return stats.get('playCount', 0)
    return 0

# ─── METHOD 1: Embed page visits ───
print('\n--- METHOD 1: Embed page visits ---')
embed_url = f'https://www.tiktok.com/embed/v2/{video_id}'
before = baseline_count()
print(f'Before: {before}')
for i in range(20):
    s = requests.Session()
    r = s.get(embed_url, headers={'User-Agent': UA}, timeout=15)
    time.sleep(0.5)
after = baseline_count()
print(f'After 20 embed visits: {after} (diff: {after - before})')

# ─── METHOD 2: Video CDN partial requests ───
print('\n--- METHOD 2: Fetch page, extract video CDN URL, request it ---')
before = baseline_count()
print(f'Before: {before}')
for i in range(20):
    s = requests.Session()
    r = s.get(VIDEO_SHORT_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15, allow_redirects=True)
    uni_match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>', r.text, re.DOTALL)
    if uni_match:
        decoded = unquote(uni_match.group(1))
        data = json.loads(decoded)
        item_struct = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {})
        video_data = item_struct.get('video', {})
        play_addr = video_data.get('playAddr', video_data.get('play_addr', {}))
        if isinstance(play_addr, dict):
            urls = play_addr.get('url_list', [])
            if urls:
                vurl = urls[0]
                try:
                    vr = s.get(vurl, headers={
                        'User-Agent': UA,
                        'Referer': 'https://www.tiktok.com/',
                        'Range': 'bytes=0-50000',
                    }, timeout=15)
                    print(f'  {i+1}: video req status={vr.status_code}, got {len(vr.content)} bytes')
                except Exception as e:
                    print(f'  {i+1}: video req error: {e}')
    time.sleep(0.3)
after = baseline_count()
print(f'After 20 CDN requests: {after} (diff: {after - before})')

# ─── METHOD 3: Tea SDK events with proper app_id ───
print('\n--- METHOD 3: Tea SDK video_play events ---')
before = baseline_count()
print(f'Before: {before}')
for i in range(20):
    s = requests.Session()
    webid = str(7600000000000000000 + i * 123456789)
    r_page = s.get(VIDEO_SHORT_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15, allow_redirects=True)
    csrf = s.cookies.get('tt_csrf_token', '')
    ttwid = s.cookies.get('ttwid', '')
    
    event_payload = {
        "events": [
            {
                "event": "video_play",
                "params": json.dumps({
                    "group_id": video_id,
                    "play_mode": "global_play",
                    "is_dark": "0",
                    "is_login": "0",
                    "enter_method": "video_detail",
                    "is_mute": "0",
                    "page_name": "video_detail",
                    "num_video_played": "1",
                    "item_list_index": "0",
                }),
                "local_time_ms": str(int(time.time() * 1000)),
            }
        ],
        "header": {
            "aid": "1988",
            "app_name": "tiktok_web",
            "channel": "pc_web",
            "device_platform": "web_pc",
            "os": "windows",
            "browser_name": "Mozilla",
            "browser_version": "125.0.0.0",
            "language": "en",
            "region": "US",
            "web_id": webid,
            "user_unique_id": webid,
            "tz_name": "America/New_York",
        },
        "user": {
            "user_unique_id": webid,
            "web_id": webid,
        },
    }
    
    try:
        r_tea = s.post(
            'https://mcs.tiktokw.us/event/',
            headers={
                'User-Agent': UA,
                'Content-Type': 'text/plain;charset=UTF-8',
                'Origin': 'https://www.tiktok.com',
                'Referer': resolved,
            },
            json=event_payload,
            timeout=15,
        )
        print(f'  {i+1}: tea status={r_tea.status_code}, resp={r_tea.text[:80]}')
    except Exception as e:
        print(f'  {i+1}: tea error: {e}')
    time.sleep(0.3)
after = baseline_count()
print(f'After 20 tea events: {after} (diff: {after - before})')

# ─── METHOD 4: Starling event (tiktokv.us) ───
print('\n--- METHOD 4: Starling/tiktokv.us monitoring events ---')
before = baseline_count()
print(f'Before: {before}')
for i in range(20):
    s = requests.Session()
    webid = str(7700000000000000000 + i * 987654321)
    now = int(time.time() * 1000)
    
    try:
        r = s.post(
            'https://mcs.tiktokw.us/event/',
            headers={
                'User-Agent': UA,
                'Content-Type': 'text/plain;charset=UTF-8',
                'Origin': 'https://www.tiktok.com',
                'Referer': resolved,
            },
            json={
                "events": [
                    {
                        "event": "video_play",
                        "params": json.dumps({
                            "group_id": video_id,
                            "play_mode": "global_play",
                            "is_dark": "0",
                            "is_login": "0",
                            "enter_method": "video_detail",
                            "is_mute": "0",
                            "page_name": "video_detail",
                        }),
                        "local_time_ms": str(now + i),
                    }
                ],
                "header": {
                    "aid": "1988",
                    "app_name": "tiktok_web",
                    "channel": "pc_web",
                    "device_platform": "web_pc",
                    "os": "windows",
                    "web_id": webid,
                    "user_unique_id": webid,
                },
            },
            timeout=15,
        )
    except:
        pass
    
    try:
        r2 = s.post(
            'https://mcs.tiktokw.us/list/',
            headers={
                'User-Agent': UA,
                'Content-Type': 'text/plain;charset=UTF-8',
                'Origin': 'https://www.tiktok.com',
                'Referer': resolved,
            },
            json={
                "events": [
                    {
                        "event": "video_play",
                        "params": json.dumps({
                            "group_id": video_id,
                            "page_name": "video_detail",
                        }),
                        "local_time_ms": str(now + i),
                    }
                ],
                "header": {
                    "aid": "1988",
                    "app_name": "tiktok_web",
                    "web_id": webid,
                    "user_unique_id": webid,
                },
            },
            timeout=15,
        )
    except:
        pass
    time.sleep(0.2)
after = baseline_count()
print(f'After 20 starling events: {after} (diff: {after - before})')

# ─── METHOD 5: Check what oembed returns ───
print('\n--- METHOD 5: OEmbed API (might show view count changes) ---')
for i in range(3):
    r = requests.get(
        f'https://www.tiktok.com/oembed?url={resolved}',
        headers={'User-Agent': UA},
        timeout=15,
    )
    try:
        d = r.json()
        print(f'  oembed: title={d.get("title","?")[:40]}, author={d.get("author_name","?")}')
    except:
        print(f'  oembed status: {r.status_code}')
    time.sleep(1)

# ─── Final count ───
final = baseline_count()
print(f'\n{"="*60}')
print(f'INITIAL: {count} | FINAL: {final} | TOTAL DIFF: {final - count}')
print(f'{"="*60}')
