import requests
import re
import json
import time
from urllib.parse import unquote

VIDEO_URL = 'https://www.tiktok.com/@guarddiszen/video/7645452587629661470'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'

def get_play_count():
    s = requests.Session()
    r = s.get(VIDEO_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15)
    uni_match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>', r.text, re.DOTALL)
    if uni_match:
        decoded = unquote(uni_match.group(1))
        data = json.loads(decoded)
        stats = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {}).get('stats', {})
        return stats.get('playCount', 0)
    return 0

def get_video_urls():
    s = requests.Session()
    r = s.get(VIDEO_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15)
    uni_match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>', r.text, re.DOTALL)
    if uni_match:
        decoded = unquote(uni_match.group(1))
        data = json.loads(decoded)
        item_struct = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {})
        video_data = item_struct.get('video', {})
        
        urls = {}
        play_addr = video_data.get('playAddr', {})
        if isinstance(play_addr, str):
            urls['playAddr'] = play_addr
        elif isinstance(play_addr, dict):
            ul = play_addr.get('url_list', [])
            if ul:
                urls['playAddr'] = ul[0]
        
        download_addr = video_data.get('downloadAddr', {})
        if isinstance(download_addr, str):
            urls['downloadAddr'] = download_addr
        elif isinstance(download_addr, dict):
            ul = download_addr.get('url_list', [])
            if ul:
                urls['downloadAddr'] = ul[0]
        
        struct = video_data.get('PlayAddrStruct', {})
        if isinstance(struct, dict):
            ul = struct.get('UrlList', [])
            if ul:
                urls['PlayAddrStruct'] = ul[0]
        
        return urls
    return {}

print('Getting video URLs...')
video_urls = get_video_urls()
for k, v in video_urls.items():
    print(f'  {k}: {v[:100]}')

before = get_play_count()
print(f'\nStarting play count: {before}')

print('\n--- TEST A: 50x page visit only ---')
for i in range(50):
    s = requests.Session()
    s.get(VIDEO_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15)
after_a = get_play_count()
print(f'After 50 page visits: {after_a} (diff: {after_a - before})')

print('\n--- TEST B: 50x page visit + video CDN partial download ---')
before_b = get_play_count()
play_url = video_urls.get('playAddr', '')
if play_url:
    for i in range(50):
        s = requests.Session()
        s.get(VIDEO_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15)
        try:
            r = s.get(play_url, headers={
                'User-Agent': UA,
                'Referer': 'https://www.tiktok.com/',
                'Accept': '*/*',
                'Accept-Encoding': 'identity',
            }, timeout=15, stream=True)
            count = 0
            for chunk in r.iter_content(chunk_size=8192):
                count += len(chunk)
                if count >= 50000:
                    break
            r.close()
        except:
            pass
        if (i+1) % 10 == 0:
            mid = get_play_count()
            print(f'  {i+1}/50: count now={mid} (running diff: {mid - before_b})')
else:
    print('No playAddr URL found!')

after_b = get_play_count()
print(f'After 50 page+CDN: {after_b} (diff: {after_b - before_b})')

print('\n--- TEST C: 50x CDN-only requests (no page visit) ---')
before_c = get_play_count()
if play_url:
    for i in range(50):
        s = requests.Session()
        try:
            r = s.get(play_url, headers={
                'User-Agent': UA,
                'Referer': 'https://www.tiktok.com/',
            }, timeout=15, stream=True)
            count = 0
            for chunk in r.iter_content(chunk_size=8192):
                count += len(chunk)
                if count >= 50000:
                    break
            r.close()
        except:
            pass
        if (i+1) % 10 == 0:
            mid = get_play_count()
            print(f'  {i+1}/50: count now={mid} (running diff: {mid - before_c})')

after_c = get_play_count()
print(f'After 50 CDN-only: {after_c} (diff: {after_c - before_c})')

print(f'\n{"="*60}')
print(f'START: {before} | END: {after_c} | TOTAL DIFF: {after_c - before}')
