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
        remove_fc(d); time.sleep(0.5)
        inp = d.find_element(By.ID, 'captchatoken')
        d.execute_script(
            "arguments[0].value=arguments[1];arguments[0].dispatchEvent(new Event('input',{bubbles:true}));arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
            inp, cleaned)
        time.sleep(1)
        dismiss_alerts(d); remove_fc(d)
        print('Submitting...')
        d.execute_script("$('form[action=\"/\"]').trigger('submit');")
        time.sleep(8)
        dismiss_alerts(d); remove_fc(d); time.sleep(1)
        body = d.find_element(By.TAG_NAME, 'body').text.lower()
        if 'views' in body and 'updated' in body:
            print('UNLOCKED!'); return True
        print(f'Not unlocked: {body[:80]}')
        d.refresh(); time.sleep(5); dismiss_alerts(d)
    return False

d = setup_driver()
try:
    d.get('https://zefoy.com')
    time.sleep(5)
    dismiss_alerts(d); remove_fc(d)

    if not solve_captcha(d):
        print('Captcha failed'); d.quit(); sys.exit(1)

    remove_fc(d); time.sleep(1)

    # Check form submit handlers attached via jQuery
    handlers = d.execute_script("""
        var form = document.querySelector('form[action="c2VuZC9mb2xeb3dlcnNfdGlrdG9V"]');
        var events = $._data ? $._data(form, 'events') : null;
        var result = {};
        if (events) {
            for (var key in events) {
                result[key] = events[key].map(function(h) {
                    return h.handler ? h.handler.toString().substring(0, 300) : 'no handler';
                });
            }
        }
        return result;
    """)
    print(f'Form jQuery handlers: {handlers}')

    # Check the button's handlers too
    btn_handlers = d.execute_script("""
        var btn = document.querySelector('.t-views-menu .disableButton');
        var events = $._data ? $._data(btn, 'events') : null;
        var result = {};
        if (events) {
            for (var key in events) {
                result[key] = events[key].map(function(h) {
                    return h.handler ? h.handler.toString().substring(0, 500) : 'no handler';
                });
            }
        }
        return result;
    """)
    print(f'Button jQuery handlers: {btn_handlers}')

    # Check document-level click handlers
    doc_handlers = d.execute_script("""
        var events = $._data ? $._data(document, 'events') : null;
        var result = {};
        if (events) {
            for (var key in events) {
                result[key] = events[key].length + ' handlers';
                result[key + '_first'] = events[key][0].handler ? events[key][0].handler.toString().substring(0, 200) : 'none';
            }
        }
        return result;
    """)
    print(f'Document jQuery handlers: {doc_handlers}')

    # Try: submit the form via jQuery trigger (not button click)
    d.execute_script("document.querySelector('.t-views-button').click();")
    time.sleep(2)
    dismiss_alerts(d); remove_fc(d)
    d.execute_script("var m=document.querySelector('.t-views-menu');if(m)m.setAttribute('style','display:block !important;');")
    time.sleep(1)

    # Set URL value
    d.execute_script("""
        var inp=document.querySelector('.t-views-menu input');
        inp.value=arguments[0];
        inp.dispatchEvent(new Event('input',{bubbles:true}));
        inp.dispatchEvent(new Event('change',{bubbles:true}));
    """, VIDEO_URL)
    time.sleep(1)

    # Clear ajax log
    d.execute_script('window._ajaxLog=[];')

    # Try method 1: jQuery form submit
    print('Method 1: jQuery form submit...')
    d.execute_script("$('form[action=\"c2VuZC9mb2xeb3dlcnNfdGlrdG9V\"]').trigger('submit');")
    time.sleep(6)
    ajax1 = d.execute_script('return JSON.stringify(window._ajaxLog);')
    print(f'  AJAX: {ajax1}')

    # Try method 2: form.submit() native
    print('Method 2: native form.submit()...')
    d.execute_script('window._ajaxLog=[];')
    d.execute_script("document.querySelector('form[action=\"c2VuZC9mb2xeb3dlcnNfdGlrdG9V\"]').submit();")
    time.sleep(6)
    ajax2 = d.execute_script('return JSON.stringify(window._ajaxLog);')
    print(f'  AJAX: {ajax2}')
    # Check if page changed
    cur_url = d.current_url
    print(f'  URL: {cur_url}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    time.sleep(2)
    try: d.quit()
    except: pass
