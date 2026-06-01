import requests, re, json
from urllib.parse import unquote

URL = 'https://www.tiktok.com/@guarddiszen1/video/7645679725960056095'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
r = requests.get(URL, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15)
print('Status:', r.status_code)

pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>'
uni_match = re.search(pattern, r.text, re.DOTALL)
if uni_match:
    decoded = unquote(uni_match.group(1))
    data = json.loads(decoded)
    stats = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {}).get('stats', {})
    print('Stats:', json.dumps(stats, indent=2))
    item = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {})
    print('Video duration:', item.get('video', {}).get('duration', 'N/A'))
else:
    print('No universal data found')
