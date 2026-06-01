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

    print('Removing FC + making views menu visible...')
    d.execute_script("""
        document.querySelectorAll('.fc-dialog-overlay,.fc-monetization-dialog-container,.fc-message-root,[id*="fc-focus-trap"]').forEach(function(el) { el.remove(); });
        
        var menu = document.querySelector('.t-views-menu');
        if (menu) {
            menu.style.display = 'block';
            menu.classList.remove('nonec');
        }
    """)
    time.sleep(2)

    print('Views menu display:', d.execute_script("return getComputedStyle(document.querySelector('.t-views-menu')).display;"))
    
    print('Entering URL...')
    d.execute_script("""
        var menu = document.querySelector('.t-views-menu');
        var input = menu.querySelector('input');
        input.value = arguments[0];
        input.dispatchEvent(new Event('input', {bubbles: true}));
        input.dispatchEvent(new Event('change', {bubbles: true}));
    """, VIDEO_URL)
    time.sleep(1)

    print('Intercepting AJAX...')
    d.execute_script("""
        window._ajaxLog = [];
        var origAjax = $.ajax;
        $.ajax = function(opts) {
            window._ajaxLog.push({url: opts.url, type: opts.type, dataType: opts.dataType});
            var origSuccess = opts.success;
            var origError = opts.error;
            opts.success = function(resp) {
                window._ajaxLog.push({url: opts.url, success: true, response: String(resp).substring(0, 500)});
                if (origSuccess) origSuccess.apply(this, arguments);
            };
            opts.error = function(xhr, status, err) {
                window._ajaxLog.push({url: opts.url, error: true, status: status});
                if (origError) origError.apply(this, arguments);
            };
            return origAjax.apply(this, arguments);
        };
    """)

    print('Clicking Search via jQuery form submit...')
    d.execute_script("""
        var form = document.querySelector('.t-views-menu form');
        if (form && typeof $ !== 'undefined') {
            $(form).trigger('submit');
        } else if (form) {
            form.submit();
        }
    """)

    for i in range(15):
        time.sleep(2)
        log = d.execute_script("return window._ajaxLog;")
        if log and len(log) > 0:
            for entry in log:
                print(f'  AJAX: {entry}')
            break

    time.sleep(5)
    for _ in range(5):
        try:
            WebDriverWait(d, 1).until(EC.alert_is_present())
            d.switch_to.alert.dismiss()
        except:
            break

    d.execute_script("""
        document.querySelectorAll('.fc-dialog-overlay,.fc-monetization-dialog-container,.fc-message-root,[id*="fc-focus-trap"]').forEach(function(el) { el.remove(); });
        var menu = document.querySelector('.t-views-menu');
        if (menu) {
            menu.style.display = 'block';
            menu.classList.remove('nonec');
        }
    """)

    print('\nFull views menu HTML after search:')
    menu_html = d.execute_script("""
        var menu = document.querySelector('.t-views-menu');
        return menu ? menu.innerHTML.substring(0, 3000) : 'not found';
    """)
    print(menu_html[:2000])

    print('\nAll elements in views menu with text:')
    elements = d.execute_script("""
        var menu = document.querySelector('.t-views-menu');
        if (!menu) return [];
        var result = [];
        menu.querySelectorAll('*').forEach(function(el) {
            if (el.textContent.trim() && el.children.length === 0) {
                result.push({tag: el.tagName, text: el.textContent.trim().substring(0, 50), display: getComputedStyle(el).display});
            }
        });
        return result;
    """)
    for el in elements:
        print(f'  {el["tag"]}: "{el["text"]}" disp={el["display"]}')

finally:
    time.sleep(2)
    d.quit()
