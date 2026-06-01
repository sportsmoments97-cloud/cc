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

    if len(cleaned) < 4:
        print('Too short')
        d.quit()
        exit()

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

    print('Submitting form...')
    d.execute_script("$('form[action=\"/\"]').trigger('submit');")
    time.sleep(8)
    for _ in range(5):
        try:
            WebDriverWait(d, 1).until(EC.alert_is_present())
            d.switch_to.alert.dismiss()
        except:
            break

    print('Testing googlefc API...')
    fc_info = d.execute_script("""
        var result = {};
        try {
            if (window.googlefc) {
                result.keys = Object.keys(window.googlefc);
                result.ConsentStatusEnum = window.googlefc.ConsentStatusEnum;
                result.AdBlockerStatusEnum = window.googlefc.AdBlockerStatusEnum;
                result.WhitelistStatusEnum = window.googlefc.WhitelistStatusEnum;
                result.AllowAdsStatusEnum = window.googlefc.AllowAdsStatusEnum;
                result.MessageTypeEnum = window.googlefc.MessageTypeEnum;
                result.callbackQueue = window.googlefc.callbackQueue ? window.googlefc.callbackQueue.length : 0;
                
                if (window.googlefc.getGoogleConsentModeValues) {
                    result.consentValues = window.googlefc.getGoogleConsentModeValues();
                }
            }
        } catch(e) { result.error = e.message; }
        
        try {
            if (window.googlefc && window.googlefc.__fci) {
                result.__fci = typeof window.googlefc.__fci;
            }
        } catch(e) { result.__fci_error = e.message; }
        
        return result;
    """)
    print(f'googlefc info: {json.dumps(fc_info, indent=2, default=str)[:1000]}')

    print('\nTrying to signal consent via googlefc...')
    consent_results = d.execute_script("""
        var results = [];
        
        try {
            if (window.googlefc && window.googlefc.callbackQueue) {
                window.googlefc.callbackQueue.push({
                    CONSENT_DATA_READY: function() {
                        results.push('CONSENT_DATA_READY callback added');
                    }
                });
            }
        } catch(e) { results.push('callbackQueue error: ' + e.message); }
        
        try {
            if (window.__tcfapi) {
                results.push('__tcfapi exists');
                window.__tcfapi('addEventListener', 2, function(tcData, success) {
                    results.push('tcfapi event: success=' + success + ' eventStatus=' + tcData.eventStatus + ' tcString=' + (tcData.tcString || '').substring(0, 50));
                });
            } else {
                results.push('no __tcfapi');
            }
        } catch(e) { results.push('__tcfapi error: ' + e.message); }
        
        try {
            if (window.__gpp) {
                results.push('__gpp exists');
            } else {
                results.push('no __gpp');
            }
        } catch(e) { results.push('__gpp error: ' + e.message); }
        
        try {
            if (window.__uspapi) {
                results.push('__uspapi exists');
                window.__uspapi('getUSPData', 1, function(data, success) {
                    results.push('uspapi: success=' + success + ' data=' + JSON.stringify(data));
                });
            } else {
                results.push('no __uspapi');
            }
        } catch(e) { results.push('__uspapi error: ' + e.message); }
        
        try {
            var consentData = {
                tcString: 'CPXxRfAPXxRfAAfK BENAOAFgABAGYABwAQAqAAAYA',
                addtlConsent: '1~',
                gdprApplies: false,
                eventStatus: 'tcloaded'
            };
            window.postMessage({__tcfapiCall: {command: 'addEventListener', parameter: consentData, version: 2}}, '*');
            results.push('Posted tcfapi consent message');
        } catch(e) { results.push('postMessage error: ' + e.message); }
        
        return results;
    """)
    for r in consent_results:
        print(f'  {r}')

    time.sleep(3)

    print('\nTrying: set FC cookie + refresh...')
    d.execute_script("""
        document.cookie = 'FCCDCF=%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5B32%2C%22%5B%5C%22d7a8b900-7c3c-4ab3-9f0e-f4b3a3e5e5a8%5C%22%2C%5B' + Date.now() + '%2C575000000%5D%5D%22%5D%5D%5D;path=/;max-age=86400';
        document.cookie = 'fc_unlocked=1;path=/;max-age=86400';
    """)
    time.sleep(1)
    d.refresh()
    time.sleep(8)
    for _ in range(5):
        try:
            WebDriverWait(d, 1).until(EC.alert_is_present())
            d.switch_to.alert.dismiss()
        except:
            break

    body = d.find_element(By.TAG_NAME, 'body').text.lower()
    print(f'After refresh+cookie: {body[:200]}')

    has_btn = d.execute_script("return !!document.querySelector('.t-views-button');")
    print(f'Has views button: {has_btn}')

    if 'unlock' in body or 'short ad' in body:
        print('FC wall still present after cookie refresh')
        
        print('\nTrying: manually dismiss FC via SDK call...')
        d.execute_script("""
            try {
                if (window.__tcfapi) {
                    window.__tcfapi('addEventListener', 2, function(tcData, success) {
                        if (success && tcData.eventStatus === 'tcloaded') {
                            window.__tcfapi('removeEventListener', 2, function() {}, tcData.listenerId);
                        }
                    });
                }
            } catch(e) {}
            
            try {
                if (window.googlefc) {
                    window.googlefc.callbackQueue = window.googlefc.callbackQueue || [];
                    window.googlefc.callbackQueue.push({
                        CONSENT_DATA_READY: function() {}
                    });
                }
            } catch(e) {}
        """)

    print('\nFinal state check...')
    d.execute_script("""
        document.querySelectorAll('.fc-dialog-overlay,.fc-monetization-dialog-container,.fc-message-root,[id*="fc-focus-trap"]').forEach(function(el) { el.remove(); });
    """)
    time.sleep(2)
    
    body = d.find_element(By.TAG_NAME, 'body').text.lower()
    print(f'Body: {body[:300]}')

    btn_count = d.execute_script("""
        var btns = document.querySelectorAll('.t-views-button, .t-hearts-button, .t-followers-button, .t-shares-button, .t-favorites-button, .t-comments-button');
        return btns.length;
    """)
    print(f'Service buttons found: {btn_count}')

    all_btns = d.execute_script("""
        var btns = document.querySelectorAll('button');
        var result = [];
        btns.forEach(function(b) {
            if (b.offsetWidth > 0 && b.textContent.trim()) {
                result.push(b.textContent.trim().substring(0, 30));
            }
        });
        return result;
    """)
    print(f'All visible buttons: {all_btns}')

finally:
    time.sleep(2)
    d.quit()
