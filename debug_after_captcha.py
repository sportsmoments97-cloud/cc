import os, sys, io, base64, time, re, json, requests
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

    if captcha_b64:
        r = requests.post('https://api.ocr.space/parse/image',
            data={'base64Image': f'data:image/png;base64,{captcha_b64}', 'language': 'eng', 'isOverlayRequired': 'false', 'scale': 'true', 'OCREngine': '2'},
            headers={'apikey': OCR_KEY}, timeout=15)
        text = r.json()['ParsedResults'][0]['ParsedText'].strip()
        cleaned = re.sub(r'[^a-zA-Z]', '', text).lower()
        print(f'Captcha OCR: "{text}" -> "{cleaned}"')

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

        print('Intercepting AJAX before submit...')
        d.execute_script("""
            window._ajaxLog = [];
            (function() {
                var orig = XMLHttpRequest.prototype.send;
                XMLHttpRequest.prototype.send = function(body) {
                    window._ajaxLog.push({url: this._url || 'unknown', method: this._method || 'unknown', body: body});
                    this.addEventListener('load', function() {
                        window._ajaxLog.push({url: this._url || 'unknown', status: this.status, response: this.responseText.substring(0, 500)});
                    });
                    orig.apply(this, arguments);
                };
                var origOpen = XMLHttpRequest.prototype.open;
                XMLHttpRequest.prototype.open = function(method, url) {
                    this._url = url;
                    this._method = method;
                    origOpen.apply(this, arguments);
                };
            })();
        """)

        print('Submitting form...')
        d.execute_script("document.querySelector('form[action=\"/\"]').submit();")
        
        for i in range(15):
            time.sleep(2)
            for _ in range(3):
                try:
                    WebDriverWait(d, 0.5).until(EC.alert_is_present())
                    d.switch_to.alert.dismiss()
                except:
                    break
            
            body_text = d.find_element(By.TAG_NAME, 'body').text
            url = d.current_url
            ajax_log = d.execute_script("return window._ajaxLog || [];")
            
            print(f'  t={i*2}s url={url} body="{body_text[:80]}" ajax_count={len(ajax_log)}')
            if ajax_log:
                for entry in ajax_log[-3:]:
                    print(f'    ajax: {entry}')

            if 'tiktok' in body_text.lower() or ('views' in body_text.lower()):
                print('SERVICES FOUND!')
                break

        print('\nFinal page source (first 2000 chars):')
        print(d.page_source[:2000])

        print('\nAll buttons:')
        for btn in d.find_elements(By.CSS_SELECTOR, 'button'):
            if btn.is_displayed():
                print(f'  Button: "{btn.text}" class="{btn.get_attribute("class")}"')

        print('\nAll visible elements with text:')
        for el in d.find_elements(By.CSS_SELECTOR, 'div,span,p,h1,h2,h3,h4'):
            text = el.text.strip()
            if text and len(text) < 100 and el.is_displayed():
                print(f'  <{el.tag_name}>: "{text}"')

finally:
    time.sleep(2)
    d.quit()
