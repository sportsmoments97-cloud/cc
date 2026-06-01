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
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = {runtime: {}};
        """
    })
    return driver

before = get_play_count()
print(f'Before: {before}')

print('\n--- TEST: 5 separate Chrome sessions, each watching 10s ---')
for run in range(5):
    driver = None
    try:
        driver = create_driver()
        driver.get(VIDEO_URL)
        
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "video")))
        except:
            pass
        
        video_elements = driver.find_elements(By.TAG_NAME, "video")
        if video_elements:
            driver.execute_script("""
                var vid = arguments[0];
                vid.muted = true;
                vid.play();
                vid.currentTime = 2;
            """, video_elements[0])
        
        time.sleep(10)
        
        play_count_after = get_play_count()
        print(f'  Run {run+1}: playCount={play_count_after} (cumulative diff: {play_count_after - before})')
        
    except Exception as e:
        print(f'  Run {run+1}: error - {e}')
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

after = get_play_count()
print(f'\nAfter 5 Chrome sessions: {after} (diff: {after - before})')

if after == before:
    print('\n--- SAME IP ISSUE: Trying with page refreshes instead of new sessions ---')
    driver = None
    try:
        driver = create_driver()
        
        for run in range(5):
            driver.get(VIDEO_URL)
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "video")))
            except:
                pass
            
            video_elements = driver.find_elements(By.TAG_NAME, "video")
            if video_elements:
                driver.execute_script("""
                    var vid = arguments[0];
                    vid.muted = true;
                    vid.play();
                """, video_elements[0])
            
            time.sleep(8)
            
            play_count_mid = get_play_count()
            print(f'  Refresh {run+1}: playCount={play_count_mid} (diff: {play_count_mid - before})')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

final = get_play_count()
print(f'\nFINAL: {final} (total diff: {final - before})')
