import requests
import re
import json
import time
from urllib.parse import unquote

VIDEO_URL = 'https://www.tiktok.com/@guarddiszen/video/7645452587629661470'
VIDEO_ID = '7645452587629661470'
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

def get_video_cdn_url():
    s = requests.Session()
    r = s.get(VIDEO_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15)
    uni_match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>', r.text, re.DOTALL)
    if uni_match:
        decoded = unquote(uni_match.group(1))
        data = json.loads(decoded)
        item_struct = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {})
        video_data = item_struct.get('video', {})
        
        play_addr = video_data.get('playAddr', {})
        if isinstance(play_addr, dict):
            urls = play_addr.get('url_list', [])
            if urls:
                return urls[0], s
        
        download_addr = video_data.get('downloadAddr', {})
        if isinstance(download_addr, dict):
            urls = download_addr.get('url_list', [])
            if urls:
                return urls[0], s
    return None, s

before = get_play_count()
print(f'Before: {before}')

cdn_url, session = get_video_cdn_url()
if cdn_url:
    print(f'Got CDN URL (first 100): {cdn_url[:100]}')
else:
    print('No CDN URL found!')
    exit()

print('\n--- Sending 50 video CDN requests with fresh sessions each time ---')
successes = 0
for i in range(50):
    try:
        s = requests.Session()
        r = s.get(cdn_url, headers={
            'User-Agent': UA,
            'Referer': 'https://www.tiktok.com/',
            'Accept': '*/*',
            'Accept-Encoding': 'identity',
        }, timeout=15, stream=True)
        
        content_length = r.headers.get('Content-Length', '?')
        status = r.status_code
        content_type = r.headers.get('Content-Type', '?')
        
        downloaded = 0
        for chunk in r.iter_content(chunk_size=1024):
            downloaded += len(chunk)
            if downloaded >= 50000:
                r.close()
                break
        
        successes += 1
        if (i + 1) % 10 == 0:
            print(f'  {i+1}/50 done (successes: {successes})')
    except Exception as e:
        print(f'  {i+1}: error - {e}')

after = get_play_count()
print(f'\nAfter 50 CDN hits: {after} (diff: {after - before})')

print('\n--- Now try with 50 fresh sessions + fresh CDN URL each time ---')
before2 = get_play_count()
print(f'Before round 2: {before2}')
for i in range(50):
    try:
        cdn_url2, _ = get_video_cdn_url()
        if cdn_url2:
            s = requests.Session()
            r = s.get(cdn_url2, headers={
                'User-Agent': UA,
                'Referer': 'https://www.tiktok.com/',
                'Accept': '*/*',
            }, timeout=15, stream=True)
            downloaded = 0
            for chunk in r.iter_content(chunk_size=1024):
                downloaded += len(chunk)
                if downloaded >= 30000:
                    r.close()
                    break
        if (i + 1) % 10 == 0:
            print(f'  {i+1}/50 done')
    except Exception as e:
        print(f'  {i+1}: error - {e}')

after2 = get_play_count()
print(f'\nAfter 50 fresh CDN hits: {after2} (diff: {after2 - before2})')

print(f'\n{"="*60}')
print(f'TOTAL: started at {before}, ended at {after2}')
print(f'{"="*60}')
