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

    d.execute_script("""
        var selectors = ['.fc-dialog-overlay','.fc-monetization-dialog-container','.fc-message-root'];
        selectors.forEach(function(s) {
            document.querySelectorAll(s).forEach(function(el) { el.remove(); });
        });
    """)
    time.sleep(2)

    print('=== Service cards HTML ===')
    cards_html = d.execute_script("""
        var cards = document.querySelectorAll('.colsmenu, .card-body, .card');
        var result = [];
        cards.forEach(function(c) {
            if (c.textContent.includes('Views') || c.textContent.includes('views')) {
                result.push({
                    tag: c.tagName,
                    class: c.className,
                    id: c.id,
                    html: c.innerHTML.substring(0, 1000),
                    text: c.textContent.substring(0, 200)
                });
            }
        });
        return result;
    """)
    for c in cards_html:
        print(f'\n{c["tag"]}.{c["class"][:40]}:')
        print(f'  Text: {c["text"][:100]}')
        print(f'  HTML: {c["html"][:500]}')

    print('\n\n=== All elements containing "Views" ===')
    views_elements = d.execute_script("""
        var result = [];
        var all = document.querySelectorAll('*');
        all.forEach(function(el) {
            if (el.childNodes.length <= 3 && el.textContent.match(/views/i) && el.textContent.length < 100) {
                result.push({
                    tag: el.tagName, class: el.className, id: el.id,
                    text: el.textContent.trim(),
                    display: getComputedStyle(el).display,
                    visibility: getComputedStyle(el).visibility,
                    opacity: getComputedStyle(el).opacity,
                    pointerEvents: getComputedStyle(el).pointerEvents,
                    html: el.outerHTML.substring(0, 500)
                });
            }
        });
        return result;
    """)
    for el in views_elements:
        print(f'\n{el["tag"]}.{el["class"][:30]}: "{el["text"]}" disp={el["display"]} vis={el["visibility"]} opacity={el["opacity"]} pointer={el["pointerEvents"]}')
        print(f'  HTML: {el["html"][:300]}')

    print('\n\n=== Find hidden service panels ===')
    panels = d.execute_script("""
        var result = [];
        var divs = document.querySelectorAll('div[style*="display"], div[style*="none"], .collapse, .panel, [id*="views"], [id*="tiktok"]');
        divs.forEach(function(d) {
            var cs = getComputedStyle(d);
            result.push({
                tag: d.tagName, class: d.className, id: d.id,
                display: cs.display, visibility: cs.visibility,
                width: d.offsetWidth, height: d.offsetHeight,
                text: d.textContent.substring(0, 80).trim()
            });
        });
        return result.slice(0, 20);
    """)
    for p in panels:
        print(f'  {p["tag"]}.{p["class"][:30]} id={p["id"][:20]} disp={p["display"]} {p["width"]}x{p["height"]} "{p["text"][:50]}"')

finally:
    time.sleep(2)
    d.quit()
