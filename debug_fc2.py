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

    print('Submitting via jQuery trigger...')
    d.execute_script("$('form[action=\"/\"]').trigger('submit');")
    
    time.sleep(5)
    for _ in range(5):
        try:
            WebDriverWait(d, 1).until(EC.alert_is_present())
            d.switch_to.alert.dismiss()
        except:
            break

    print('Investigating FC wall...')
    
    fc_info = d.execute_script("""
        var result = {};
        result.windowFC = typeof window.FundingChoices;
        result.googlefc = typeof window.googlefc;
        result.googletag = typeof window.googletag;
        result.googletagAPI = (typeof window.googletag !== 'undefined') ? typeof window.googletag.apiReady : 'N/A';
        result.pubadsReady = (typeof window.googletag !== 'undefined' && window.googletag.pubads) ? typeof window.googletag.pubads().getTargeting : 'N/A';
        
        var fcElements = document.querySelectorAll('[class*="fc-"], [id*="fc-"]');
        result.fcElementCount = fcElements.length;
        result.fcElements = [];
        fcElements.forEach(function(el) {
            result.fcElements.push({
                tag: el.tagName,
                class: el.className,
                id: el.id,
                visible: el.offsetWidth > 0 && el.offsetHeight > 0,
                width: el.offsetWidth,
                height: el.offsetHeight,
                text: el.textContent.substring(0, 100).trim()
            });
        });
        
        var iframes = document.querySelectorAll('iframe');
        result.iframes = [];
        iframes.forEach(function(f) {
            result.iframes.push({src: f.src.substring(0, 200), id: f.id, class: f.className, width: f.width, height: f.height});
        });
        
        result.cookies = document.cookie;
        
        return result;
    """)
    
    print(f'Window.FundingChoices: {fc_info["windowFC"]}')
    print(f'Window.googlefc: {fc_info["googlefc"]}')
    print(f'Googletag: {fc_info["googletag"]}')
    print(f'Googletag API ready: {fc_info["googletagAPI"]}')
    print(f'Pubads ready: {fc_info["pubadsReady"]}')
    print(f'FC elements: {fc_info["fcElementCount"]}')
    for el in fc_info.get('fcElements', []):
        print(f'  {el["tag"]}.{el["class"][:50]} visible={el["visible"]} {el["width"]}x{el["height"]} text="{el["text"][:60]}"')
    print(f'Iframes: {len(fc_info.get("iframes", []))}')
    for f in fc_info.get('iframes', []):
        print(f'  {f["id"] or f["class"]} src={f["src"][:80]}')
    
    print('\nTrying FC SDK interactions...')
    fc_result = d.execute_script("""
        var results = [];
        
        try {
            if (window.googlefc) {
                results.push('googlefc exists: ' + JSON.stringify(Object.keys(window.googlefc)));
            }
        } catch(e) { results.push('googlefc error: ' + e.message); }
        
        try {
            if (window.FundingChoices) {
                results.push('FundingChoices: ' + JSON.stringify(Object.keys(window.FundingChoices)));
                if (window.FundingChoices.rejectConsent) {
                    window.FundingChoices.rejectConsent();
                    results.push('Called rejectConsent');
                }
            }
        } catch(e) { results.push('FundingChoices error: ' + e.message); }
        
        try {
            var fcBtn = document.querySelector('.fc-rewarded-ad-button');
            if (fcBtn) {
                results.push('FC button found: ' + fcBtn.textContent.substring(0, 50));
                results.push('FC button onclick: ' + (fcBtn.onclick ? fcBtn.onclick.toString() : 'none'));
                
                var parent = fcBtn.parentElement;
                var chain = [];
                while (parent && chain.length < 5) {
                    chain.push(parent.tagName + '.' + (parent.className || '').substring(0, 30));
                    parent = parent.parentElement;
                }
                results.push('FC button parent chain: ' + chain.join(' > '));
            } else {
                results.push('No FC button found');
            }
        } catch(e) { results.push('FC button error: ' + e.message); }
        
        try {
            var dialogs = document.querySelectorAll('[class*="fc-dialog"]');
            results.push('FC dialogs: ' + dialogs.length);
            dialogs.forEach(function(d, i) {
                results.push('Dialog ' + i + ': ' + d.className + ' display=' + getComputedStyle(d).display + ' visibility=' + getComputedStyle(d).visibility);
            });
        } catch(e) { results.push('Dialog error: ' + e.message); }
        
        try {
            var overlay = document.querySelector('.fc-dialog-overlay');
            if (overlay) {
                var cs = getComputedStyle(overlay);
                results.push('Overlay: display=' + cs.display + ' z-index=' + cs.zIndex + ' position=' + cs.position);
            }
        } catch(e) { results.push('Overlay error: ' + e.message); }
        
        return results;
    """)
    for r in fc_result:
        print(f'  {r}')

    print('\nAttempting: remove FC overlay then check page...')
    d.execute_script("""
        var overlay = document.querySelector('.fc-dialog-overlay');
        if (overlay) overlay.remove();
        var dialogs = document.querySelectorAll('.fc-monetization-dialog-container, .fc-message-root');
        dialogs.forEach(function(d) { d.remove(); });
    """)
    time.sleep(3)
    
    body = d.find_element(By.TAG_NAME, 'body').text.lower()
    print(f'Body after removal: {body[:200]}')
    
    if 'tiktok' not in body or not any(x in body for x in ['views','followers','hearts']):
        print('\nServices still not visible. Checking page source...')
        src = d.page_source.lower()[:3000]
        if 'tiktok' in src and 'views' in src:
            print('Services in page source!')
        else:
            print('No services in source either.')
        
        print('\nTrying: click FC button and watch...')
        d.refresh()
        time.sleep(5)
        for _ in range(5):
            try:
                WebDriverWait(d, 1).until(EC.alert_is_present())
                d.switch_to.alert.dismiss()
            except:
                break
        
        try:
            fc_btn = d.find_element(By.CSS_SELECTOR, '.fc-rewarded-ad-button')
            print(f'FC button: "{fc_btn.text}"')
            d.execute_script("arguments[0].click();", fc_btn)
            print('Clicked FC button')
            
            main = d.current_window_handle
            for i in range(30):
                time.sleep(1)
                for _ in range(2):
                    try:
                        WebDriverWait(d, 0.5).until(EC.alert_is_present())
                        d.switch_to.alert.dismiss()
                    except:
                        break
                
                handles = d.window_handles
                if len(handles) > 1:
                    print(f'New window at {i}s!')
                    for h in handles:
                        if h != main:
                            d.switch_to.window(h)
                            print(f'  Popup URL: {d.current_url}')
                            time.sleep(5)
                            for _ in range(60):
                                time.sleep(1)
                                try: d.current_url
                                except: break
                            try: d.close()
                            except: pass
                            d.switch_to.window(main)
                    break
                
                body = d.find_element(By.TAG_NAME, 'body').text.lower()
                if 'tiktok' in body and any(x in body for x in ['views','followers','hearts']):
                    print(f'UNLOCKED at {i}s!')
                    break
        except Exception as e:
            print(f'FC button error: {e}')

finally:
    time.sleep(2)
    d.quit()
