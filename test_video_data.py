import requests
import re
import json
import time
from urllib.parse import unquote

VIDEO_URL = 'https://www.tiktok.com/@guarddiszen/video/7645452587629661470'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'

s = requests.Session()
r = s.get(VIDEO_URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15)

uni_match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>', r.text, re.DOTALL)
if uni_match:
    decoded = unquote(uni_match.group(1))
    data = json.loads(decoded)
    scope = data.get('__DEFAULT_SCOPE__', {})
    vd = scope.get('webapp.video-detail', {})
    item_info = vd.get('itemInfo', {})
    item_struct = item_info.get('itemStruct', {})
    video_data = item_struct.get('video', {})
    
    print('Video data keys:', list(video_data.keys()))
    
    for key in video_data:
        val = video_data[key]
        if isinstance(val, dict):
            sub_keys = list(val.keys())[:10]
            print(f'\n  {key} (dict): keys={sub_keys}')
            if 'url_list' in val:
                urls = val['url_list']
                for u in urls[:2]:
                    print(f'    URL: {u[:120]}')
            if 'url_key' in val:
                print(f'    url_key: {val["url_key"]}')
        elif isinstance(val, str) and ('http' in val or 'cdn' in val):
            print(f'\n  {key} (url): {val[:120]}')
        elif isinstance(val, list):
            print(f'\n  {key} (list): len={len(val)}')
            for item in val[:2]:
                if isinstance(item, str):
                    print(f'    [{item[:120]}')
        else:
            val_str = str(val)[:80]
            print(f'\n  {key}: {val_str}')
