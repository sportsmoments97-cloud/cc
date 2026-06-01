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

options = Options()
options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--headless=new')
options.add_argument('--disable-gpu')
options.add_argument('--disable-notifications')
options.add_experimental_option('prefs', {'profile.default_content_setting_values.notifications': 2})
options.add_argument('--window-size=1366,768')

d = webdriver.Chrome(options=options)
d.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
})

d.get('https://zefoy.com')
time.sleep(5)

# Dismiss alerts
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
for _ in range(5):
    try:
        WebDriverWait(d, 1).until(EC.alert_is_present())
        d.switch_to.alert.dismiss()
    except:
        break

title = d.title
print(f'Title: {title}')

b64 = d.execute_script("""
var img=document.getElementById('captcha-img');
if(!img||!img.naturalWidth)return null;
var c=document.createElement('canvas');c.width=img.naturalWidth;c.height=img.naturalHeight;
c.getContext('2d').drawImage(img,0,0);return c.toDataURL('image/png').split(',')[1];
""")
print(f'Captcha b64: {len(b64) if b64 else "NONE"} chars')

if b64:
    r = requests.post('https://api.ocr.space/parse/image',
        data={'base64Image': f'data:image/png;base64,{b64}', 'language': 'eng', 'OCREngine': 2},
        headers={'apikey': 'K84731687888957'}, timeout=15)
    text = r.json().get('ParsedResults', [{}])[0].get('ParsedText', '').strip()
    print(f'OCR result: {text}')

d.quit()
