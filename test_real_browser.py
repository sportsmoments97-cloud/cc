import time
import re
import json
import requests
from urllib.parse import unquote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

before = get_play_count()
print(f'Before: {before}')

print('Testing different videos to see if ANY video count changes...')

test_videos = [
    ('https://www.tiktok.com/@khaby.lame/video/7270803387986492187', 'Khaby Lame popular'),
    ('https://www.tiktok.com/@charlidamelio/video/7270803387986492187', 'Charli (may 404)'),
]

for url, label in test_videos:
    count = get_play_count_for(url)
    print(f'  {label}: playCount={count}')

def get_play_count_for(url):
    s = requests.Session()
    r = s.get(url, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15)
    uni_match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>', r.text, re.DOTALL)
    if uni_match:
        decoded = unquote(uni_match.group(1))
        data = json.loads(decoded)
        stats = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {}).get('stats', {})
        return stats.get('playCount', 0)
    return 'N/A'

print('\n--- Now checking: does the count change for OUR video after just waiting? ---')
for i in range(3):
    count = get_play_count()
    print(f'  Check {i+1}: {count}')
    time.sleep(2)

print('\n--- Testing: manually open this URL in YOUR real browser, then check count ---')
print(f'URL: {VIDEO_URL}')
print('Open it, watch a few seconds, then press Enter here...')
input('Press Enter after watching in your real browser...')
after_real = get_play_count()
print(f'After your real browser visit: {after_real} (diff: {after_real - before})')
