import os, sys, io, base64, time, re, json, requests

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def flush(self):
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

sys.stdout = Unbuffered(sys.stdout)
sys.stderr = Unbuffered(sys.stderr)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

VIDEO_URL = 'https://www.tiktok.com/@guarddiszen1/video/7645679725960056095'
OCR_KEY = 'K84731687888957'

options = Options()
options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--window-size=1366,768")
d = webdriver.Chrome(options=options)

try:
    d.get('https://zefoy.com')
    time.sleep(5)
    for _ in range(5):
        try:
            WebDriverWait(d, 1).until(EC.alert_is_present())
            d.switch_to.alert.dismiss()
        except:
            break
    time.sleep(2)

    captcha_b64 = d.execute_script("""
        var img = document.getElementById('captcha-img');
        if (!img || !img.naturalWidth) return null;
        var canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        return canvas.toDataURL('image/png').split(',')[1];
    """)

    r = requests.post('https://api.ocr.space/parse/image',
        data={'base64Image': f'data:image/png;base64,{captcha_b64}', 'language': 'eng', 'isOverlayRequired': 'false', 'scale': 'true', 'OCREngine': '2'},
        headers={'apikey': OCR_KEY}, timeout=15)
    text = r.json()['ParsedResults'][0]['ParsedText'].strip()
    cleaned = re.sub(r'[^a-zA-Z]', '', text).lower()
    print(f'Captcha: {text} -> {cleaned}')

    if len(cleaned) < 4:
        print('Too short, aborting')
        d.quit()
        exit()

    inp = d.find_element(By.ID, 'captchatoken')
    d.execute_script("""
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
    """, inp, cleaned)
    time.sleep(1)
    for _ in range(5):
        try:
            WebDriverWait(d, 1).until(EC.alert_is_present())
            d.switch_to.alert.dismiss()
        except:
            break

    print('Using zefoy native form handler via click on submit button...')
    
    d.execute_script("""
        window._pageReloaded = false;
        var origReload = window.location.reload;
        window.location.reload = function() {
            window._pageReloaded = true;
            window.location.href = window.location.href;
        };
    """)

    d.execute_script("""
        var form = document.querySelector('form[action="/"]');
        if (form) {
            var submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) {
                submitBtn.click();
            } else {
                var btn = form.querySelector('button');
                if (btn) btn.click();
                else form.submit();
            }
        }
    """)

    print('Waiting for page reload...')
    for i in range(30):
        time.sleep(1)
        reloaded = d.execute_script("return window._pageReloaded;")
        if reloaded:
            print(f'Page reloaded at {i}s')
            break
        try:
            body = d.find_element(By.TAG_NAME, 'body').text.lower()
            if body and 'enter the word' not in body:
                print(f'Body changed at {i}s: {body[:60]}')
        except:
            pass

    time.sleep(5)
    for _ in range(5):
        try:
            WebDriverWait(d, 1).until(EC.alert_is_present())
            d.switch_to.alert.dismiss()
        except:
            break

    print(f'URL: {d.current_url}')
    print(f'Body text: {d.find_element(By.TAG_NAME, "body").text[:200]}')

    has_services = d.execute_script("""
        return !!document.querySelector('.t-views-button, .t-views-menu, .colsmenu');
    """)
    print(f'Has services: {has_services}')

    if not has_services:
        print('No services, page might need reload. Doing full reload...')
        d.refresh()
        time.sleep(5)
        for _ in range(5):
            try:
                WebDriverWait(d, 1).until(EC.alert_is_present())
                d.switch_to.alert.dismiss()
            except:
                break
        
        has_services = d.execute_script("return !!document.querySelector('.t-views-button, .colsmenu');")
        print(f'Has services after refresh: {has_services}')
        body = d.find_element(By.TAG_NAME, 'body').text.lower()
        print(f'Body: {body[:200]}')

    if has_services:
        print('\nRemoving FC overlay...')
        d.execute_script("""
            document.querySelectorAll('.fc-dialog-overlay,.fc-monetization-dialog-container,.fc-message-root,[id*="fc-focus-trap"]').forEach(function(el) { el.remove(); });
        """)
        time.sleep(1)

        print('Clicking Views button...')
        d.execute_script("document.querySelector('.t-views-button').click();")
        time.sleep(3)

        menu_display = d.execute_script("""
            var menu = document.querySelector('.t-views-menu');
            return menu ? getComputedStyle(menu).display : 'not found';
        """)
        print(f'Views menu display: {menu_display}')

        if menu_display == 'none':
            print('Menu still hidden, forcing visible...')
            d.execute_script("""
                var menu = document.querySelector('.t-views-menu');
                if (menu) {
                    menu.style.display = 'block !important';
                    menu.classList.remove('nonec');
                    menu.setAttribute('style', 'display: block !important;');
                }
            """)
            time.sleep(1)

        d.execute_script("""
            document.querySelectorAll('.fc-dialog-overlay,.fc-monetization-dialog-container,.fc-message-root,[id*="fc-focus-trap"]').forEach(function(el) { el.remove(); });
        """)

        menu_html = d.execute_script("return document.querySelector('.t-views-menu') ? document.querySelector('.t-views-menu').innerHTML.substring(0, 1000) : 'N/A';")
        print(f'Menu HTML: {menu_html[:500]}')

finally:
    time.sleep(2)
    d.quit()
