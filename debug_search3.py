import sys, io, time, re, requests

class U:
    def __init__(self, s): self.s = s
    def write(self, d): self.s.write(d); self.s.flush()
    def flush(self): self.s.flush()
    def __getattr__(self, a): return getattr(self.s, a)

sys.stdout = U(sys.stdout)
sys.stderr = U(sys.stderr)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

OCR_KEY = 'K84731687888957'
VIDEO_URL = 'https://www.tiktok.com/@guarddiszen1/video/7645679725960056095'

def ocr(b64):
    r = requests.post('https://api.ocr.space/parse/image',
        data={'base64Image': f'data:image/png;base64,{b64}', 'language': 'eng', 'OCREngine': 2},
        headers={'apikey': OCR_KEY}, timeout=15)
    data = r.json()
    if data.get('ParsedResults') and data['ParsedResults'][0].get('ParsedText'):
        return data['ParsedResults'][0]['ParsedText'].strip()
    return ''

def setup_driver():
    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1366,768')
    options.add_argument('--disable-notifications')
    options.add_experimental_option('prefs', {'profile.default_content_setting_values.notifications': 2})
    d = webdriver.Chrome(options=options)
    d.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
    })
    # AJAX interceptor
    d.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': """
window._ajaxLog = [];
(function() {
    var origOpen = XMLHttpRequest.prototype.open;
    var origSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(method, url) {
        this._logUrl = url; this._logMethod = method;
        return origOpen.apply(this, arguments);
    };
    XMLHttpRequest.prototype.send = function(body) {
        window._ajaxLog.push({method: this._logMethod, url: this._logUrl, body: body, time: Date.now()});
        this.addEventListener('load', function() {
            var entry = window._ajaxLog[window._ajaxLog.length - 1];
            entry.status = this.status;
            entry.response = this.responseText.substring(0, 500);
        });
        return origSend.apply(this, arguments);
    };
    var origFetch = window.fetch;
    window.fetch = function(url, opts) {
        window._ajaxLog.push({method: (opts && opts.method) || 'GET', url: typeof url === 'string' ? url : url.url, body: opts && opts.body, time: Date.now(), type: 'fetch'});
        return origFetch.apply(this, arguments);
    };
})();
"""})
    return d

def dismiss_alerts(d):
    for _ in range(5):
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            WebDriverWait(d, 1).until(EC.alert_is_present())
            d.switch_to.alert.dismiss()
        except:
            break

def remove_fc(d):
    d.execute_script("""
        ['.fc-dialog-overlay','.fc-monetization-dialog-container','.fc-message-root',
         '[id*="fc-focus-trap"]','.fc-dialog-content'].forEach(function(s) {
            document.querySelectorAll(s).forEach(function(e) { e.remove(); });
        });
    """)

def solve_captcha(d):
    last_src = None
    for attempt in range(20):
        time.sleep(3)
        dismiss_alerts(d)

        src = d.execute_script("var img=document.getElementById('captcha-img');return img?img.src:null;")
        if src == last_src:
            d.refresh(); time.sleep(5); dismiss_alerts(d); continue
        last_src = src

        b64 = d.execute_script("""
            var img=document.getElementById('captcha-img');
            if(!img||!img.naturalWidth)return null;
            var c=document.createElement('canvas');c.width=img.naturalWidth;c.height=img.naturalHeight;
            c.getContext('2d').drawImage(img,0,0);return c.toDataURL('image/png').split(',')[1];
        """)
        if not b64:
            d.refresh(); time.sleep(5); dismiss_alerts(d); continue

        text = ocr(b64)
        cleaned = re.sub(r'[^a-zA-Z]', '', text).lower()
        print(f'Captcha: {text} -> {cleaned}')

        if len(cleaned) < 4:
            d.refresh(); time.sleep(5); dismiss_alerts(d); continue

        remove_fc(d)
        time.sleep(0.5)
        inp = d.find_element(By.ID, 'captchatoken')
        d.execute_script(
            "arguments[0].value=arguments[1];arguments[0].dispatchEvent(new Event('input',{bubbles:true}));arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
            inp, cleaned)
        time.sleep(1)
        dismiss_alerts(d)
        remove_fc(d)

        print('Submitting...')
        d.execute_script("$('form[action=\"/\"]').trigger('submit');")
        time.sleep(8)
        dismiss_alerts(d)
        remove_fc(d)
        time.sleep(1)

        body = d.find_element(By.TAG_NAME, 'body').text.lower()
        if 'views' in body and 'updated' in body:
            print('UNLOCKED!')
            return True
        print(f'Not unlocked: {body[:80]}')
        d.refresh(); time.sleep(5); dismiss_alerts(d)

    return False

d = setup_driver()
try:
    d.get('https://zefoy.com')
    time.sleep(5)
    dismiss_alerts(d)
    remove_fc(d)

    if not solve_captcha(d):
        print('Captcha failed')
        d.quit()
        sys.exit(1)

    remove_fc(d)
    time.sleep(1)

    # Click Views
    d.execute_script("document.querySelector('.t-views-button').click();")
    time.sleep(2)
    dismiss_alerts(d)
    remove_fc(d)

    # Force menu visible
    d.execute_script("var m=document.querySelector('.t-views-menu');if(m)m.setAttribute('style','display:block !important;');")
    time.sleep(1)

    # Get form info
    form_info = d.execute_script("""
        var m=document.querySelector('.t-views-menu');
        var form=m.querySelector('form');
        var inp=form.querySelector('input');
        var btn=form.querySelector('.disableButton');
        return {
            action: form.getAttribute('action'),
            method: form.getAttribute('method'),
            inputName: inp ? inp.name : null,
            inputType: inp ? inp.type : null,
            inputPH: inp ? inp.placeholder : null,
            btnFound: !!btn,
            btnText: btn ? btn.textContent.trim() : null,
            btnDisabled: btn ? btn.disabled : null
        };
    """)
    print(f'Form info: {form_info}')

    # Clear ajax log
    d.execute_script('window._ajaxLog=[];')

    # Enter URL
    d.execute_script("""
        var m=document.querySelector('.t-views-menu');
        var inp=m.querySelector('input');
        inp.value=arguments[0];
        inp.dispatchEvent(new Event('input',{bubbles:true}));
        inp.dispatchEvent(new Event('change',{bubbles:true}));
    """, VIDEO_URL)
    time.sleep(1)

    # Try jQuery trigger on Search button instead of click
    print('Clicking Search via jQuery...')
    d.execute_script("""
        var m=document.querySelector('.t-views-menu');
        var btn=m.querySelector('.disableButton');
        if(typeof $ !== 'undefined') {
            $(btn).trigger('click');
        } else {
            btn.click();
        }
    """)
    time.sleep(8)
    dismiss_alerts(d)
    remove_fc(d)

    # Check AJAX log
    ajax = d.execute_script('return JSON.stringify(window._ajaxLog,null,2);')
    print(f'AJAX log: {ajax}')

    # Check response div
    resp = d.execute_script("""
        var r=document.getElementById('c2VuZC9mb2xeb3dlcnNfdGlrdG9V');
        return r ? {html:r.innerHTML.substring(0,500),text:r.textContent.substring(0,200),display:getComputedStyle(r).display} : null;
    """)
    print(f'Response div: {resp}')

    # Check full menu
    menu = d.execute_script("return document.querySelector('.t-views-menu').innerHTML;")
    print(f'Full menu HTML: {menu[:2000]}')

    # Also check if any new buttons appeared
    btns = d.execute_script("""
        var m=document.querySelector('.t-views-menu');
        var btns=m.querySelectorAll('button,input[type=submit],a.btn');
        var result=[];
        for(var i=0;i<btns.length;i++){
            result.push({tag:btns[i].tagName,text:btns[i].textContent.trim(),class:btns[i].className,display:getComputedStyle(btns[i]).display,disabled:btns[i].disabled});
        }
        return result;
    """)
    print(f'All buttons: {btns}')

    # Check if there are any error messages
    errs = d.execute_script("""
        var m=document.querySelector('.t-views-menu');
        var alerts=m.querySelectorAll('.alert,.error,.text-danger,.invalid-feedback');
        var result=[];
        for(var i=0;i<alerts.length;i++) result.push(alerts[i].textContent.trim());
        return result;
    """)
    print(f'Errors: {errs}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    time.sleep(2)
    try:
        d.quit()
    except:
        pass
