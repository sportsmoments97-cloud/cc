import os, sys, io, base64, time, re, json, requests, random
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

VIDEO_URL = 'https://www.tiktok.com/@guarddiszen1/video/7645679725960056095'
SCREENSHOT_DIR = r'C:\Users\bt398\Downloads\tiktok bot\debug'

def js_click(d, e):
    d.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", e)

def remove_ads(d):
    d.execute_script("""
        document.querySelectorAll('iframe').forEach(f => {
            if (f.src.includes('doubleclick')||f.src.includes('googleads')||f.id.includes('aswift')) f.remove();
        });
        document.querySelectorAll('ins,[id*="google"],[class*="ad-"],[class*="adsense"],[id*="ad-"],[class*="google-auto"]').forEach(e => e.remove());
    """)

def screenshot(d, name):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    path = os.path.join(SCREENSHOT_DIR, f'{name}.png')
    d.save_screenshot(path)
    print(f'  Screenshot: {path}')

def solve_captcha_ocr_space(captcha_b64):
    try:
        r = requests.post('https://api.ocr.space/parse/image', 
            data={'base64Image': f'data:image/png;base64,{captcha_b64}', 'language': 'eng', 'isOverlayRequired': 'false', 'scale': 'true'},
            headers={'apikey': 'K84731687888957'}, timeout=15)
        data = r.json()
        if data.get('ParsedResults'):
            return data['ParsedResults'][0].get('ParsedText', '').strip()
    except Exception as e:
        print(f'  OCR error: {e}')
    return None

def get_count(url):
    try:
        UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        s = requests.Session()
        r = s.get(url, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15)
        pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>'
        m = re.search(pattern, r.text, re.DOTALL)
        if m:
            from urllib.parse import unquote
            data = json.loads(unquote(m.group(1)))
            stats = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {}).get('stats', {})
            return stats.get('playCount', 0)
    except:
        pass
    return -1

class ZefoyBot:
    def __init__(self, video_url):
        self.video_url = video_url
        self.driver = None
        self.sent = 0
    
    def setup(self):
        options = Options()
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1366,768")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        prefs = {"profile.default_content_setting_values.notifications": 2}
        options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        })
    
    def solve_captcha(self):
        for attempt in range(15):
            print(f'Captcha #{attempt+1}...')
            time.sleep(2)
            
            imgs = self.driver.find_elements(By.TAG_NAME, 'img')
            captcha_img = None
            for img in imgs:
                src = img.get_attribute('src') or ''
                if '_CAPTCHA' in src or 'captcha' in src.lower() or 'rand' in src.lower():
                    captcha_img = img
                    break
            
            if not captcha_img:
                for img in imgs:
                    if img.size['width'] > 80 and img.size['width'] < 300 and img.size['height'] > 20 and img.size['height'] < 100:
                        captcha_img = img
                        break
            
            if not captcha_img:
                screenshot(self.driver, f'no_captcha_{attempt}')
                print('  No captcha img found')
                time.sleep(2)
                continue
            
            b64 = base64.b64encode(captcha_img.screenshot_as_png).decode()
            result = solve_captcha_ocr_space(b64)
            if not result or len(result.strip()) < 2:
                screenshot(self.driver, f'ocr_fail_{attempt}')
                self.driver.refresh()
                time.sleep(3)
                remove_ads(self.driver)
                continue
            
            result = result.strip().replace(' ', '')
            print(f'  OCR: "{result}"')
            
            inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"],input[type="search"],input:not([type])')
            inp = None
            for i in inputs:
                if i.is_displayed():
                    inp = i
                    break
            if not inp:
                continue
            
            self.driver.execute_script("""
                arguments[0].value=arguments[1];
                arguments[0].dispatchEvent(new Event('input',{bubbles:true}));
                arguments[0].dispatchEvent(new Event('change',{bubbles:true}));
            """, inp, result)
            time.sleep(0.5)
            
            screenshot(self.driver, f'before_submit_{attempt}')
            remove_ads(self.driver)
            time.sleep(0.5)
            
            submits = self.driver.find_elements(By.CSS_SELECTOR, 'button')
            for btn in submits:
                t = btn.text.lower().strip()
                cls = btn.get_attribute('class') or ''
                if 'submit' in t or 'submit' in cls or 'check' in t or 'verify' in t or 'go' in t:
                    js_click(self.driver, btn)
                    print(f'  Clicked submit: "{btn.text}"')
                    break
            else:
                for btn in submits:
                    if btn.is_displayed():
                        js_click(self.driver, btn)
                        print(f'  Clicked btn: "{btn.text}"')
                        break
            
            time.sleep(5)
            screenshot(self.driver, f'after_submit_{attempt}')
            
            try:
                body = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
            except:
                body = ''
            
            if 'unlock' in body or 'short ad' in body or 'watch' in body:
                print('  Need to watch ad')
                return 'need_ad'
            
            if any(kw in body for kw in ['tiktok views', 'tiktok followers', 'tiktok hearts', 'tiktok shares', 'tiktok favorites', 'tiktok livestream']):
                print('  Services visible - unlocked!')
                return 'unlocked'
            
            if 'wrong' in body or 'incorrect' in body or 'invalid' in body:
                print('  Wrong captcha, retrying...')
                self.driver.refresh()
                time.sleep(3)
                remove_ads(self.driver)
                continue
            
            print(f'  Unknown state, body preview: {body[:150]}')
            self.driver.refresh()
            time.sleep(3)
            remove_ads(self.driver)
        
        return 'failed'
    
    def watch_ad_and_unlock(self):
        print('Ad unlock flow...')
        main_handle = self.driver.current_window_handle
        
        screenshot(self.driver, 'before_ad_click')
        
        remove_ads(self.driver)
        time.sleep(1)
        
        all_btns = self.driver.find_elements(By.CSS_SELECTOR, 'button, a, div[onclick]')
        ad_btn = None
        for btn in all_btns:
            t = (btn.text or '').lower().strip()
            if any(x in t for x in ['view', 'watch', 'ad', 'unlock', 'continue']):
                ad_btn = btn
                print(f'  Ad button: "{btn.text}"')
                break
        
        if not ad_btn:
            all_clickable = self.driver.find_elements(By.CSS_SELECTOR, '[role="button"], .btn, a.btn')
            for el in all_clickable:
                t = (el.text or '').lower()
                if t and any(x in t for x in ['view', 'watch', 'ad', 'unlock']):
                    ad_btn = el
                    print(f'  Clickable: "{el.text}"')
                    break
        
        if not ad_btn:
            print('  No ad button found! Dumping all buttons:')
            for b in all_btns[:20]:
                print(f'    "{b.text[:60]}" displayed={b.is_displayed()}')
            screenshot(self.driver, 'no_ad_btn')
            return False
        
        remove_ads(self.driver)
        js_click(self.driver, ad_btn)
        print('  Clicked ad button')
        time.sleep(3)
        
        screenshot(self.driver, 'after_ad_click')
        
        popup_handles = [h for h in self.driver.window_handles if h != main_handle]
        
        if popup_handles:
            print(f'  {len(popup_handles)} popup(s) opened')
            for ph in popup_handles:
                self.driver.switch_to.window(ph)
                url = self.driver.current_url
                print(f'  Popup URL: {url[:100]}')
                
                if 'googleads' in url or 'doubleclick' in url or 'ad' in url.lower():
                    print('  Ad popup - waiting for it to load...')
                    for i in range(40):
                        time.sleep(1)
                        try:
                            self.driver.current_url
                        except:
                            break
                    
                    try:
                        body = self.driver.find_element(By.TAG_NAME, 'body')
                        links = body.find_elements(By.TAG_NAME, 'a')
                        if links:
                            js_click(self.driver, links[0])
                            print('  Clicked ad link inside popup')
                            time.sleep(10)
                    except:
                        pass
                    
                    time.sleep(5)
                    try:
                        self.driver.close()
                    except:
                        pass
                else:
                    try:
                        self.driver.close()
                    except:
                        pass
            
            self.driver.switch_to.window(main_handle)
        else:
            print('  No popup - ad might be inline')
            
            for i in range(20):
                time.sleep(1)
                try:
                    body = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
                    if 'tiktok' in body and any(x in body for x in ['views', 'followers', 'hearts']):
                        print('  Unlocked after inline ad!')
                        screenshot(self.driver, 'unlocked_inline')
                        return True
                except:
                    pass
        
        time.sleep(5)
        screenshot(self.driver, 'after_ad_wait')
        
        try:
            body = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
            print(f'  Body after ad: {body[:200]}')
            
            if 'tiktok' in body and any(x in body for x in ['views', 'followers', 'hearts', 'shares']):
                print('  Services unlocked!')
                return True
            
            if 'unlock' in body or 'short ad' in body:
                print('  Still locked, trying second ad click...')
                
                remove_ads(self.driver)
                time.sleep(1)
                
                btns2 = self.driver.find_elements(By.CSS_SELECTOR, 'button, a, div[onclick]')
                for btn in btns2:
                    t = (btn.text or '').lower().strip()
                    if any(x in t for x in ['view', 'watch', 'ad', 'unlock', 'continue', 'retry']):
                        js_click(self.driver, btn)
                        print(f'  Second click: "{btn.text}"')
                        time.sleep(20)
                        break
                
                for h in self.driver.window_handles:
                    if h != main_handle:
                        self.driver.switch_to.window(h)
                        time.sleep(15)
                        try: self.driver.close()
                        except: pass
                        self.driver.switch_to.window(main_handle)
                
                time.sleep(5)
                screenshot(self.driver, 'after_second_ad')
                return True
        except:
            pass
        
        return False
    
    def find_and_click_views(self):
        print('Looking for Views service...')
        time.sleep(3)
        remove_ads(self.driver)
        screenshot(self.driver, 'services_page')
        
        try:
            html = self.driver.page_source
            with open(os.path.join(SCREENSHOT_DIR, 'page_source.html'), 'w', encoding='utf-8') as f:
                f.write(html)
            print('  Saved page source')
        except:
            pass
        
        try:
            body = self.driver.find_element(By.TAG_NAME, 'body').text
            print(f'  Visible text: {body[:300]}')
        except:
            pass
        
        all_btns = self.driver.find_elements(By.CSS_SELECTOR, 'button')
        print(f'  Total buttons: {len(all_btns)}')
        
        view_btn = None
        
        for btn in all_btns:
            if btn.is_displayed():
                t = btn.text.strip()
                if t:
                    print(f'  Btn: "{t[:60]}"')
                    tl = t.lower()
                    if 'tiktok' in tl and 'view' in tl:
                        view_btn = btn
        
        if not view_btn:
            for btn in all_btns:
                if btn.is_displayed():
                    t = btn.text.strip().lower()
                    if 'view' in t and ('tiktok' in t or 'video' in t or t == 'views'):
                        view_btn = btn
                        break
        
        if not view_btn:
            for btn in all_btns:
                if btn.is_displayed():
                    t = btn.text.strip().lower()
                    if 'view' in t:
                        view_btn = btn
                        break
        
        if not view_btn:
            print('  Trying XPATH...')
            for i in range(4, 12):
                try:
                    btn = self.driver.find_element(By.XPATH, f'/html/body/div[{i}]/div/div[2]/div/div/div[5]/div/button')
                    if btn.is_displayed() and btn.is_enabled():
                        view_btn = btn
                        print(f'  Found XPATH div[{i}]')
                        break
                except:
                    pass
        
        if not view_btn:
            print('  No Views button found')
            return False
        
        print(f'  Clicking: "{view_btn.text}"')
        remove_ads(self.driver)
        js_click(self.driver, view_btn)
        time.sleep(3)
        remove_ads(self.driver)
        screenshot(self.driver, 'after_views_click')
        return True
    
    def enter_url_and_search(self):
        print('Entering video URL...')
        time.sleep(2)
        
        inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"],input[type="url"],input[type="search"],input:not([type])')
        url_input = None
        for inp in inputs:
            if inp.is_displayed():
                url_input = inp
                break
        
        if not url_input:
            screenshot(self.driver, 'no_url_input')
            print('  No URL input found')
            return False
        
        self.driver.execute_script("""
            arguments[0].value=arguments[1];
            arguments[0].dispatchEvent(new Event('input',{bubbles:true}));
            arguments[0].dispatchEvent(new Event('change',{bubbles:true}));
        """, url_input, self.video_url)
        print(f'  Entered URL')
        time.sleep(1)
        
        remove_ads(self.driver)
        
        btns = self.driver.find_elements(By.CSS_SELECTOR, 'button')
        for btn in btns:
            t = btn.text.lower().strip()
            if btn.is_displayed() and ('search' in t or 'find' in t or 'submit' in t):
                js_click(self.driver, btn)
                print(f'  Clicked: "{btn.text}"')
                time.sleep(5)
                screenshot(self.driver, 'after_search')
                return True
        
        url_input.submit()
        print('  Submitted form')
        time.sleep(5)
        screenshot(self.driver, 'after_submit_url')
        return True
    
    def send_loop(self, max_sends=100):
        print('Sending views...')
        before = get_count(self.video_url)
        
        for i in range(max_sends):
            try:
                screenshot(self.driver, f'send_{i}')
                remove_ads(self.driver)
                
                btns = self.driver.find_elements(By.CSS_SELECTOR, 'button')
                sent = False
                
                for btn in btns:
                    t = btn.text.lower().strip()
                    if ('send' in t or 'submit' in t or 'go' in t) and btn.is_displayed() and btn.is_enabled():
                        js_click(self.driver, btn)
                        self.sent += 1
                        sent = True
                        print(f'  Send #{self.sent}')
                        break
                
                if not sent:
                    try:
                        body = self.driver.find_element(By.TAG_NAME, 'body').text
                        m = re.search(r'(\d+)\s*second', body, re.IGNORECASE)
                        if m:
                            w = int(m.group(1))
                            print(f'  Cooldown: {w}s')
                            time.sleep(w + 3)
                        else:
                            print(f'  No send button, body: {body[:100]}')
                            time.sleep(5)
                            screenshot(self.driver, f'stuck_{i}')
                    except:
                        time.sleep(5)
                else:
                    time.sleep(3)
                
                if self.sent > 0 and self.sent % 5 == 0:
                    c = get_count(self.video_url)
                    print(f'  Count: {c} (diff: {c - before})')
            
            except Exception as e:
                print(f'  Error: {str(e)[:80]}')
                time.sleep(5)
    
    def run(self):
        self.setup()
        before = get_count(self.video_url)
        print(f'View count before: {before}')
        
        try:
            print('Loading zefoy.com...')
            self.driver.get('https://zefoy.com')
            time.sleep(5)
            remove_ads(self.driver)
            
            try:
                WebDriverWait(self.driver, 3).until(EC.alert_is_present())
                self.driver.switch_to.alert.dismiss()
            except:
                pass
            
            result = self.solve_captcha()
            print(f'Captcha result: {result}')
            
            if result == 'need_ad':
                ok = self.watch_ad_and_unlock()
                if not ok:
                    print('Ad unlock failed')
                    return
            elif result == 'failed':
                print('Captcha failed completely')
                return
            
            remove_ads(self.driver)
            time.sleep(2)
            
            if not self.find_and_click_views():
                print('Cannot find Views service')
                return
            
            if not self.enter_url_and_search():
                print('Cannot enter URL')
                return
            
            self.send_loop()
        
        except Exception as e:
            print(f'Fatal: {e}')
            import traceback
            traceback.print_exc()
        finally:
            after = get_count(self.video_url)
            print(f'\nViews: {before} -> {after} (diff: {after-before}, sends: {self.sent})')
            time.sleep(2)
            try: self.driver.quit()
            except: pass

if __name__ == '__main__':
    bot = ZefoyBot(VIDEO_URL)
    bot.run()
