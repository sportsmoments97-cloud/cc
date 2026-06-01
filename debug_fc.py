import os, sys, io, base64, time, re, json, requests
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def dismiss_alerts(d):
    for _ in range(5):
        try:
            WebDriverWait(d, 1).until(EC.alert_is_present())
            d.switch_to.alert.dismiss()
        except:
            break

def remove_ads(d):
    d.execute_script("""
        document.querySelectorAll('iframe').forEach(f => {
            var src = f.src||'';
            var id = f.id||'';
            if (src.includes('doubleclick')||src.includes('googleads')||id.includes('aswift')) f.remove();
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
    except:
        pass
    return None

options = Options()
options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--window-size=1366,768")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-notifications")
prefs = {"profile.default_content_setting_values.notifications": 2}
options.add_experimental_option("prefs", prefs)
d = webdriver.Chrome(options=options)
d.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
})

try:
    d.get('https://zefoy.com')
    time.sleep(5)
    dismiss_alerts(d)
    remove_ads(d)
    
    print('Solving captcha...')
    for attempt in range(20):
        print(f'  #{attempt+1}')
        time.sleep(2)
        dismiss_alerts(d)
        
        imgs = d.find_elements(By.TAG_NAME, 'img')
        captcha_img = None
        for img in imgs:
            src = img.get_attribute('src') or ''
            if '_CAPTCHA' in src or 'captcha' in src.lower() or 'rand' in src.lower():
                captcha_img = img
                break
        if not captcha_img:
            for img in imgs:
                if 80 < img.size['width'] < 350 and 20 < img.size['height'] < 120:
                    captcha_img = img
                    break
        if not captcha_img:
            continue
        
        b64 = base64.b64encode(captcha_img.screenshot_as_png).decode()
        result = solve_captcha_ocr_space(b64)
        if not result or len(result.strip()) < 2:
            d.refresh()
            time.sleep(3)
            dismiss_alerts(d)
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
        dismiss_alerts(d)
        
        btns = d.find_elements(By.CSS_SELECTOR, 'button')
        for btn in btns:
            cls = btn.get_attribute('class') or ''
            if 'submit' in cls:
                d.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", btn)
                print('  Submitted')
                break
        
        time.sleep(5)
        dismiss_alerts(d)
        
        body = d.find_element(By.TAG_NAME, 'body').text.lower()
        if 'unlock' in body or 'short ad' in body:
            print('Captcha solved, need ad unlock')
            break
        if any(x in body for x in ['tiktok views', 'tiktok followers', 'tiktok hearts']):
            print('Already unlocked!')
            break
        if 'wrong' in body or 'incorrect' in body:
            d.refresh()
            time.sleep(3)
            dismiss_alerts(d)
            continue
        d.refresh()
        time.sleep(3)
        dismiss_alerts(d)
    
    print('\n=== INVESTIGATING FC SDK ===')
    
    fc_debug = d.execute_script("""
        var info = {};
        
        // Check all window properties for FC-related stuff
        info.windowKeys = Object.keys(window).filter(k => 
            k.toLowerCase().includes('fc') || 
            k.toLowerCase().includes('funding') || 
            k.toLowerCase().includes('reward') ||
            k.toLowerCase().includes('ad') ||
            k.toLowerCase().includes('googlefc')
        );
        
        // Check for Google AdSense/FundingChoices objects
        info.hasGoogleFC = typeof window.googleFC !== 'undefined';
        info.hasFundingChoices = typeof window.FundingChoices !== 'undefined';
        info.hasAdSense = typeof window.google_ad_status !== 'undefined';
        info.hasGpt = typeof window.googletag !== 'undefined';
        info.hasAdsbygoogle = typeof window.adsbygoogle !== 'undefined';
        
        // Check all scripts loaded
        var scripts = document.querySelectorAll('script[src]');
        info.scripts = [];
        scripts.forEach(function(s) {
            if (s.src.includes('fc') || s.src.includes('funding') || s.src.includes('google') || s.src.includes('adsense') || s.src.includes('doubleclick')) {
                info.scripts.push(s.src.substring(0,120));
            }
        });
        
        // Check the fc button's event listeners
        var fcBtn = document.querySelector('.fc-rewarded-ad-button, .fc-list-item-button');
        if (fcBtn) {
            info.fcBtnExists = true;
            info.fcBtnTag = fcBtn.tagName;
            info.fcBtnCls = fcBtn.className;
            info.fcBtnHtml = fcBtn.outerHTML.substring(0, 500);
            
            // Check parent elements
            var parent = fcBtn.parentElement;
            info.fcBtnParent = parent ? parent.tagName + '.' + (parent.className||'').substring(0,60) : 'none';
            info.fcBtnParentHtml = parent ? parent.outerHTML.substring(0, 500) : 'none';
            
            var grandparent = parent ? parent.parentElement : null;
            info.fcBtnGrandparent = grandparent ? grandparent.tagName + '.' + (grandparent.className||'').substring(0,60) : 'none';
            info.fcBtnGrandparentHtml = grandparent ? grandparent.outerHTML.substring(0, 800) : 'none';
            
            // Check for onclick attribute
            info.fcBtnOnclick = fcBtn.getAttribute('onclick') || 'none';
            
            // Look for the fc container/wrapper
            var fcContainer = document.querySelector('[class*="fc-consent"], [class*="fc-choice"], [id*="fc-"]');
            if (fcContainer) {
                info.fcContainer = fcContainer.tagName + '.' + (fcContainer.className||'').substring(0,60);
                info.fcContainerHtml = fcContainer.outerHTML.substring(0, 1000);
            }
        } else {
            info.fcBtnExists = false;
        }
        
        // Check for fc-dialog / fc-consent roots
        var fcRoots = document.querySelectorAll('[class*="fc-"], [id*="fc-"]');
        info.fcElements = [];
        fcRoots.forEach(function(el) {
            info.fcElements.push(el.tagName + '.' + (el.className||'').substring(0,40) + '#' + (el.id||''));
        });
        
        // Intercept any XHR/fetch to see what happens when button is clicked
        info.xhrLog = [];
        var origOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url) {
            info.xhrLog.push(method + ' ' + url.substring(0,100));
            return origOpen.apply(this, arguments);
        };
        
        return info;
    """)
    
    print(json.dumps(fc_debug, indent=2)[:3000])
    
    print('\n=== TRYING TO TRIGGER REWARDED AD ===')
    
    # Method 1: Click the fc button and monitor network
    result2 = d.execute_script("""
        var log = [];
        var fcBtn = document.querySelector('.fc-rewarded-ad-button, .fc-list-item-button');
        if (!fcBtn) return {error: 'no fc button'};
        
        // Hook into window.open to see if an ad URL is attempted
        var origOpen = window.open;
        window.open = function(url) {
            log.push('window.open called: ' + (url||'').substring(0,120));
            return origOpen.apply(this, arguments);
        };
        
        // Hook postMessage
        var origPostMessage = window.postMessage;
        window.postMessage = function(msg) {
            log.push('postMessage: ' + JSON.stringify(msg).substring(0,120));
            return origPostMessage.apply(this, arguments);
        };
        
        // Click the button
        fcBtn.click();
        log.push('clicked fc button');
        
        // Also try clicking parent
        if (fcBtn.parentElement) {
            fcBtn.parentElement.click();
            log.push('clicked parent');
        }
        
        return log;
    """)
    print(f'Click result: {result2}')
    
    time.sleep(5)
    
    # Check what happened
    after_click = d.execute_script("""
        var info = {};
        info.windowHandles = window.length;
        info.bodyText = document.body.textContent.substring(0, 300).toLowerCase();
        
        // Check if any new iframes appeared
        var iframes = document.querySelectorAll('iframe');
        info.iframes = [];
        iframes.forEach(function(f) {
            info.iframes.push({id: f.id, src: (f.src||'').substring(0,80), displayed: f.offsetWidth > 0});
        });
        
        // Check for fc dialog changes
        var fcEls = document.querySelectorAll('[class*="fc-"]');
        info.fcElements = [];
        fcEls.forEach(function(el) {
            if (el.offsetWidth > 0) {
                info.fcElements.push(el.tagName + '.' + (el.className||'').substring(0,40) + ': ' + (el.textContent||'').substring(0,60));
            }
        });
        
        // Check for rewarded ad container
        var adContainers = document.querySelectorAll('[id*="google_ads"], [id*="aswift"], [class*="ad-container"]');
        info.adContainers = adContainers.length;
        
        return info;
    """)
    print(f'\nAfter click: {json.dumps(after_click, indent=2)[:1000]}')
    
    # Method 2: Try to use googletag to trigger rewarded ad
    print('\n=== TRYING GPT REWARDED AD ===')
    gpt_result = d.execute_script("""
        var info = {};
        if (typeof googletag !== 'undefined') {
            info.gptExists = true;
            info.gptMethods = Object.keys(googletag).join(',').substring(0,200);
            
            try {
                var slots = googletag.pubads().getSlots();
                info.slotCount = slots.length;
                info.slots = slots.map(function(s) {
                    return s.getAdUnitPath();
                });
            } catch(e) {
                info.slotError = e.message;
            }
        } else {
            info.gptExists = false;
        }
        
        // Try to find the rewarded ad slot via pubads
        if (typeof googletag !== 'undefined' && googletag.pubads) {
            try {
                info.pubadsKeys = Object.keys(googletag.pubads()).join(',').substring(0,200);
            } catch(e) {}
        }
        
        return info;
    """)
    print(f'GPT: {json.dumps(gpt_result, indent=2)[:500]}')
    
    # Method 3: Try directly invoking the __fundingChoiceCalls or similar
    print('\n=== LOOKING FOR FC CALLBACKS IN PAGE ===')
    callbacks = d.execute_script("""
        var info = {};
        
        // Search for any function that might handle ad completion
        var allScripts = document.querySelectorAll('script:not([src])');
        info.inlineScriptCount = allScripts.length;
        info.fcRelated = [];
        
        allScripts.forEach(function(s) {
            var text = s.textContent || '';
            if (text.includes('fc') || text.includes('reward') || text.includes('unlock') || text.includes('funding')) {
                // Find function names
                var matches = text.match(/function\s+(\w*(?:fc|reward|unlock|ad)\w*)/gi);
                if (matches) {
                    info.fcRelated.push(matches.join(', ').substring(0,200));
                }
                
                // Find variable assignments with these keywords
                var vars = text.match(/(?:var|let|const)\s+(\w*(?:fc|reward|unlock|ad)\w*)/gi);
                if (vars) {
                    info.fcRelated.push(vars.join(', ').substring(0,200));
                }
            }
        });
        
        // Check window for any callback-like functions
        info.windowFunctions = [];
        for (var key in window) {
            try {
                if (typeof window[key] === 'function' && 
                    (key.toLowerCase().includes('ad') || key.toLowerCase().includes('unlock') || 
                     key.toLowerCase().includes('fc') || key.toLowerCase().includes('reward'))) {
                    info.windowFunctions.push(key);
                }
            } catch(e) {}
        }
        
        // Check __fundingChoiceCalls
        if (typeof window.__fundingChoiceCalls !== 'undefined') {
            info.fundingChoiceCalls = JSON.stringify(window.__fundingChoiceCalls).substring(0,500);
        }
        
        return info;
    """)
    print(f'Callbacks: {json.dumps(callbacks, indent=2)[:1000]}')
    
    # Method 4: Try to set the cookie that FC sets when ad is watched
    print('\n=== TRYING COOKIE BYPASS ===')
    cookie_result = d.execute_script("""
        var info = {};
        
        // Set various cookies that might indicate ad completion
        document.cookie = 'fc_token=1; path=/; max-age=86400';
        document.cookie = 'GFC_ad=1; path=/; max-age=86400';
        document.cookie = 'FC_ad_complete=1; path=/; max-age=86400';
        document.cookie = '__gads=1; path=/; max-age=86400';
        document.cookie = '__gpi=1; path=/; max-age=86400';
        
        // Try localStorage
        localStorage.setItem('fc_unlocked', '1');
        localStorage.setItem('ad_complete', '1');
        
        info.cookies = document.cookie;
        return info;
    """)
    print(f'Cookies set: {cookie_result}')
    
    d.refresh()
    time.sleep(5)
    dismiss_alerts(d)
    
    body = d.find_element(By.TAG_NAME, 'body').text.lower()
    print(f'\nAfter refresh with cookies: {body[:200]}')
    
    if 'tiktok' in body and any(x in body for x in ['views','followers','hearts']):
        print('COOKIE BYPASS WORKED!')
    elif 'unlock' in body or 'short ad' in body:
        print('Cookie bypass did not work - still locked')
    else:
        print('Different page state - might be unlocked')

finally:
    time.sleep(2)
    d.quit()
