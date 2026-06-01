import os, sys, io, base64, time, re, requests
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

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
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            WebDriverWait(d, 1).until(EC.alert_is_present())
            d.switch_to.alert.dismiss()
        except:
            break
    time.sleep(2)
    
    captcha_b64_canvas = d.execute_script("""
        var img = document.getElementById('captcha-img');
        var canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight);
        return canvas.toDataURL('image/png').split(',')[1];
    """)
    
    debug_dir = r'C:\Users\bt398\Downloads\tiktok bot\debug'
    os.makedirs(debug_dir, exist_ok=True)
    with open(os.path.join(debug_dir, 'captcha_canvas2.png'), 'wb') as f:
        f.write(base64.b64decode(captcha_b64_canvas))
    
    print(f'Canvas image size: {len(captcha_b64_canvas)}')
    
    r = requests.post('https://api.ocr.space/parse/image', 
        data={'base64Image': f'data:image/png;base64,{captcha_b64_canvas}', 'language': 'eng', 'isOverlayRequired': 'false', 'scale': 'true', 'OCREngine': '2'},
        headers={'apikey': 'K84731687888957'}, timeout=15)
    data = r.json()
    print(f'OCR Engine 2: {data}')
    
    r2 = requests.post('https://api.ocr.space/parse/image', 
        data={'base64Image': f'data:image/png;base64,{captcha_b64_canvas}', 'language': 'eng', 'isOverlayRequired': 'false', 'scale': 'true', 'OCREngine': '1'},
        headers={'apikey': 'K84731687888957'}, timeout=15)
    data2 = r2.json()
    print(f'OCR Engine 1: {data2}')
    
    big_canvas = d.execute_script("""
        var img = document.getElementById('captcha-img');
        var canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth * 4;
        canvas.height = img.naturalHeight * 4;
        var ctx = canvas.getContext('2d');
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        return canvas.toDataURL('image/png').split(',')[1];
    """)
    
    with open(os.path.join(debug_dir, 'captcha_big.png'), 'wb') as f:
        f.write(base64.b64decode(big_canvas))
    
    r3 = requests.post('https://api.ocr.space/parse/image', 
        data={'base64Image': f'data:image/png;base64,{big_canvas}', 'language': 'eng', 'isOverlayRequired': 'false', 'scale': 'true', 'OCREngine': '2'},
        headers={'apikey': 'K84731687888957'}, timeout=15)
    data3 = r3.json()
    print(f'OCR Engine 2 (4x): {data3}')

finally:
    time.sleep(2)
    d.quit()
