import time
import re
import json
import requests
from urllib.parse import unquote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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

def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={UA}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-images")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-sync")
    
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = {runtime: {}};
        """
    })
    return driver

print('\n--- TEST: 10x headless Chrome visits ---')
for i in range(10):
    driver = None
    try:
        driver = create_driver()
        driver.get(VIDEO_URL)
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
        except:
            pass
        
        time.sleep(3)
        
        video_elements = driver.find_elements(By.TAG_NAME, "video")
        if video_elements:
            driver.execute_script("arguments[0].play();", video_elements[0])
            time.sleep(5)
        
        print(f'  Visit {i+1}: done (video found: {len(video_elements) > 0})')
    except Exception as e:
        print(f'  Visit {i+1}: error - {e}')
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

after = get_play_count()
print(f'\nAfter 10 Chrome visits: {after} (diff: {after - before})')

print('\n--- TEST: Single Chrome visit with longer watch time ---')
driver = None
try:
    driver = create_driver()
    driver.get(VIDEO_URL)
    
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "video"))
        )
    except:
        print('  Video element not found')
    
    video_elements = driver.find_elements(By.TAG_NAME, "video")
    if video_elements:
        driver.execute_script("arguments[0].play();", video_elements[0])
        print('  Playing video for 30 seconds...')
        time.sleep(30)
    else:
        print('  No video element, waiting 30s anyway...')
        time.sleep(30)
    
    after2 = get_play_count()
    print(f'  After 1 long visit: {after2} (diff from initial: {after2 - before})')
except Exception as e:
    print(f'  Error: {e}')
finally:
    if driver:
        try:
            driver.quit()
        except:
            pass

final = get_play_count()
print(f'\n{"="*60}')
print(f'START: {before} | END: {final} | TOTAL DIFF: {final - before}')
