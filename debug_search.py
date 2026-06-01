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

def ocr_captcha(b64):
    try:
        r = requests.post('https://api.ocr.space/parse/image',
            data={'base64Image': f'data:image/png;base64,{b64}', 'language': 'eng', 'isOverlayRequired': 'true', 'scale': 'true', 'OCREngine': '2'},
            headers={'apikey': OCR_KEY}, timeout=15)
        data = r.json()
        if data.get('ParsedResults') and data['ParsedResults'][0].get('ParsedText'):
            text = data['ParsedResults'][0]['ParsedText'].strip()
            lines = data['ParsedResults'][0].get('TextOverlay', {}).get('Lines', [])
            word_count = sum(len(l.get('Words', [])) for l in lines)
            return text, word_count
    except:
        pass
    return None, 0

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

    print('Submitting...')
    d.execute_script("$('form[action=\"/\"]').trigger('submit');")
    time.sleep(5)
    for _ in range(5):
        try:
            WebDriverWait(d, 1).until(EC.alert_is_present())
            d.switch_to.alert.dismiss()
        except:
            break

    print('Removing FC overlay...')
    d.execute_script("""
        document.querySelectorAll('.fc-dialog-overlay,.fc-monetization-dialog-container,.fc-message-root,[id*="fc-focus-trap"]').forEach(function(el) { el.remove(); });
    """)
    time.sleep(2)

    print('Clicking Views button...')
    d.execute_script("document.querySelector('.t-views-button').click();")
    time.sleep(3)
    for _ in range(5):
        try:
            WebDriverWait(d, 1).until(EC.alert_is_present())
            d.switch_to.alert.dismiss()
        except:
            break

    print('Checking views menu...')
    menu = d.execute_script("""
        var menu = document.querySelector('.t-views-menu');
        return {
            exists: !!menu,
            display: menu ? getComputedStyle(menu).display : 'N/A',
            html: menu ? menu.innerHTML.substring(0, 1000) : 'N/A'
        };
    """)
    print(f'Menu: exists={menu["exists"]} display={menu["display"]}')
    print(f'Menu HTML: {menu["html"][:500]}')

    print('\nEntering URL...')
    d.execute_script("""
        var menu = document.querySelector('.t-views-menu');
        var input = menu.querySelector('input');
        input.value = arguments[0];
        input.dispatchEvent(new Event('input', {bubbles: true}));
    """, VIDEO_URL)
    time.sleep(1)

    print('Intercepting AJAX before search...')
    d.execute_script("""
        window._searchResult = null;
        window._searchError = null;
        var origAjax = $.ajax;
        $.ajax = function(opts) {
            if (opts && opts.url && opts.url.indexOf('c2VuZC9') !== -1) {
                var origSuccess = opts.success;
                opts.success = function(resp) {
                    window._searchResult = resp;
                    if (origSuccess) origSuccess(resp);
                };
                var origError = opts.error;
                opts.error = function(xhr, status, err) {
                    window._searchError = status + ': ' + err;
                    if (origError) origError(xhr, status, err);
                };
            }
            return origAjax.apply(this, arguments);
        };
    """)

    print('Clicking Search...')
    d.execute_script("""
        var btn = document.querySelector('.t-views-menu .disableButton');
        if (btn) btn.click();
        else $('form[action*="c2VuZC9"]').trigger('submit');
    """)

    for i in range(20):
        time.sleep(2)
        result = d.execute_script("return window._searchResult;")
        error = d.execute_script("return window._searchError;")
        if result is not None:
            print(f'Search result: {str(result)[:200]}')
            break
        if error is not None:
            print(f'Search error: {error}')
            break

    time.sleep(3)
    for _ in range(5):
        try:
            WebDriverWait(d, 1).until(EC.alert_is_present())
            d.switch_to.alert.dismiss()
        except:
            break

    d.execute_script("""
        document.querySelectorAll('.fc-dialog-overlay,.fc-monetization-dialog-container,.fc-message-root,[id*="fc-focus-trap"]').forEach(function(el) { el.remove(); });
    """)

    print('\nChecking views menu after search...')
    menu_html = d.execute_script("""
        var menu = document.querySelector('.t-views-menu');
        return menu ? menu.innerHTML.substring(0, 2000) : 'not found';
    """)
    print(f'Menu HTML: {menu_html[:1500]}')

    print('\nAll buttons in views menu:')
    btns = d.execute_script("""
        var menu = document.querySelector('.t-views-menu');
        if (!menu) return [];
        var btns = menu.querySelectorAll('button');
        var result = [];
        btns.forEach(function(b) {
            result.push({
                text: b.textContent.trim(),
                class: b.className,
                display: getComputedStyle(b).display,
                disabled: b.disabled,
                visible: b.offsetWidth > 0
            });
        });
        return result;
    """)
    for b in btns:
        print(f'  Button: "{b["text"]}" class={b["class"][:30]} disp={b["display"]} disabled={b["disabled"]} vis={b["visible"]}')

finally:
    time.sleep(2)
    d.quit()
