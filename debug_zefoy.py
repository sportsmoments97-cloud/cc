import os, sys, io, base64, time, re, json, requests
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

SCREENSHOT_DIR = r'C:\Users\bt398\Downloads\tiktok bot\debug'

def remove_ads(d):
    d.execute_script("""
        document.querySelectorAll('iframe').forEach(f => {
            if (f.src.includes('doubleclick')||f.src.includes('googleads')||f.id.includes('aswift')) f.remove();
        });
    """)

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

options = Options()
options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--window-size=1366,768")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
d = webdriver.Chrome(options=options)
d.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
})

try:
    d.get('https://zefoy.com')
    time.sleep(5)
    try:
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        WebDriverWait(d, 3).until(EC.alert_is_present())
        d.switch_to.alert.dismiss()
        print('Dismissed notification alert')
    except:
        pass
    remove_ads(d)
    
    for attempt in range(15):
        print(f'\nCaptcha #{attempt+1}...')
        
        imgs = d.find_elements(By.TAG_NAME, 'img')
        captcha_img = None
        for img in imgs:
            src = img.get_attribute('src') or ''
            if '_CAPTCHA' in src or 'captcha' in src.lower() or 'rand' in src.lower():
                captcha_img = img
                break
        if not captcha_img:
            for img in imgs:
                if 80 < img.size['width'] < 300 and 20 < img.size['height'] < 100:
                    captcha_img = img
                    break
        if not captcha_img:
            print('  No captcha img')
            time.sleep(2)
            continue
        
        b64 = base64.b64encode(captcha_img.screenshot_as_png).decode()
        result = solve_captcha_ocr_space(b64)
        if not result or len(result.strip()) < 2:
            d.refresh()
            time.sleep(3)
            remove_ads(d)
            continue
        
        result = result.strip().replace(' ', '')
        print(f'  OCR: "{result}"')
        
        inputs = d.find_elements(By.CSS_SELECTOR, 'input[type="text"],input[type="search"],input:not([type])')
        inp = None
        for i in inputs:
            if i.is_displayed():
                inp = i
                break
        if not inp:
            continue
        
        d.execute_script("""
            arguments[0].value=arguments[1];
            arguments[0].dispatchEvent(new Event('input',{bubbles:true}));
            arguments[0].dispatchEvent(new Event('change',{bubbles:true}));
        """, inp, result)
        time.sleep(0.5)
        
        remove_ads(d)
        time.sleep(0.5)
        
        submits = d.find_elements(By.CSS_SELECTOR, 'button')
        for btn in submits:
            if btn.is_displayed():
                d.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", btn)
                print(f'  Clicked: "{btn.text}"')
                break
        
        time.sleep(5)
        
        body = d.find_element(By.TAG_NAME, 'body').text.lower()
        if 'unlock' in body or 'short ad' in body or 'watch' in body:
            print('CAPTCHA SOLVED - need ad. Dumping page...')
            break
        if any(kw in body for kw in ['tiktok views', 'tiktok followers', 'tiktok hearts']):
            print('UNLOCKED already')
            break
        if 'wrong' in body or 'incorrect' in body:
            d.refresh()
            time.sleep(3)
            remove_ads(d)
            continue
        
        d.refresh()
        time.sleep(3)
        remove_ads(d)
    
    print('\n=== DUMPING ALL ELEMENTS ===')
    
    html = d.page_source
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    with open(os.path.join(SCREENSHOT_DIR, 'after_captcha.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print('Saved HTML source')
    
    d.save_screenshot(os.path.join(SCREENSHOT_DIR, 'after_captcha.png'))
    
    body_text = d.find_element(By.TAG_NAME, 'body').text
    print(f'\n=== VISIBLE TEXT ===\n{body_text[:1000]}')
    
    print(f'\n=== ALL CLICKABLE ELEMENTS ===')
    for tag in ['button', 'a', 'div[onclick]', 'span[onclick]', 'input[type="submit"]', '[role="button"]']:
        elems = d.find_elements(By.CSS_SELECTOR, tag)
        for e in elems:
            try:
                if e.is_displayed():
                    txt = (e.text or '').strip()[:60]
                    tag_name = e.tag_name
                    cls = (e.get_attribute('class') or '')[:40]
                    onclick = e.get_attribute('onclick') or ''
                    href = e.get_attribute('href') or ''
                    print(f'  <{tag_name}> text="{txt}" class="{cls}" onclick="{onclick[:40]}" href="{href[:40]}"')
            except:
                pass
    
    print(f'\n=== ALL IFRAMES ===')
    iframes = d.find_elements(By.TAG_NAME, 'iframe')
    for iframe in iframes:
        src = iframe.get_attribute('src') or ''
        iid = iframe.get_attribute('id') or ''
        print(f'  id="{iid}" src="{src[:80]}" displayed={iframe.is_displayed()}')
    
    print(f'\n=== JS: document.querySelectorAll("div,span,a,button") visible text ===')
    texts = d.execute_script("""
        var result = [];
        document.querySelectorAll('div,span,a,button,input').forEach(function(el) {
            if (el.offsetWidth > 0 && el.offsetHeight > 0) {
                var t = el.textContent || el.value || '';
                t = t.trim();
                if (t && t.length < 200 && t.length > 0) {
                    var tag = el.tagName.toLowerCase();
                    var cls = el.className || '';
                    if (typeof cls === 'object') cls = '';
                    result.push(tag + '.' + cls.toString().substring(0,30) + ': ' + t.substring(0,80));
                }
            }
        });
        return [...new Set(result)];
    """)
    for t in texts[:50]:
        print(f'  {t}')
    
    print('\n=== Looking for ad/unlock related elements via JS ===')
    ad_elems = d.execute_script("""
        var result = [];
        var all = document.querySelectorAll('*');
        for (var i = 0; i < all.length; i++) {
            var el = all[i];
            var t = (el.textContent || '').trim().toLowerCase();
            var style = window.getComputedStyle(el);
            if (style.display !== 'none' && style.visibility !== 'hidden' && el.offsetWidth > 0) {
                if (t.includes('ad') || t.includes('unlock') || t.includes('watch') || t.includes('short')) {
                    result.push(el.tagName + '.' + (el.className||'').toString().substring(0,30) + ': "' + t.substring(0,100) + '"');
                }
            }
        }
        return [...new Set(result)].slice(0, 30);
    """)
    for e in ad_elems:
        print(f'  {e}')

finally:
    time.sleep(2)
    d.quit()
