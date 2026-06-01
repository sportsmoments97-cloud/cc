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
        var selectors = ['.fc-dialog-overlay','.fc-monetization-dialog-container','.fc-message-root'];
        selectors.forEach(function(s) {
            document.querySelectorAll(s).forEach(function(el) { el.remove(); });
        });
    """)
    time.sleep(2)

    print('Full page text:')
    body = d.find_element(By.TAG_NAME, 'body').text
    print(body[:2000])

    print('\n\nAll buttons:')
    for btn in d.find_elements(By.CSS_SELECTOR, 'button'):
        txt = btn.text.strip()
        disp = btn.is_displayed()
        print(f'  [{disp}] "{txt}"')

    print('\n\nAll div containers:')
    divs = d.find_elements(By.CSS_SELECTOR, 'div[class*="col"],div[class*="card"],div[class*="service"],div[class*="item"]')
    for div in divs[:20]:
        if div.is_displayed():
            print(f'  .{div.get_attribute("class")[:40]}: "{div.text[:80]}"')

    print('\n\nFull HTML structure (first 5000 chars):')
    src = d.page_source
    print(src[:5000])

finally:
    time.sleep(2)
    d.quit()
