import os, sys, io, base64, time, re, requests
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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
    time.sleep(3)
    for _ in range(5):
        try:
            WebDriverWait(d, 1).until(EC.alert_is_present())
            d.switch_to.alert.dismiss()
        except:
            break
    
    info = d.execute_script("""
        var img = document.getElementById('captcha-img');
        if (!img) return {error: 'no captcha-img element'};
        return {
            src: img.src,
            naturalWidth: img.naturalWidth,
            naturalHeight: img.naturalHeight,
            width: img.width,
            height: img.height,
            complete: img.complete,
            alt: img.alt,
            currentSrc: img.currentSrc || '',
            outerHTML: img.outerHTML.substring(0, 500)
        };
    """)
    print('Captcha info:', info)
    
    if info.get('naturalWidth', 0) == 0 or not info.get('complete'):
        print('Image not loaded, waiting...')
        time.sleep(10)
        
        info2 = d.execute_script("""
            var img = document.getElementById('captcha-img');
            return {
                src: img.src,
                naturalWidth: img.naturalWidth,
                naturalHeight: img.naturalHeight,
                complete: img.complete
            };
        """)
        print('After wait:', info2)
    
    b64 = d.execute_script("""
        var img = document.getElementById('captcha-img');
        if (!img || !img.naturalWidth || img.naturalWidth == 0) return null;
        var canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        return canvas.toDataURL('image/png').split(',')[1];
    """)
    
    if b64:
        r = requests.post('https://api.ocr.space/parse/image', 
            data={'base64Image': f'data:image/png;base64,{b64}', 'language': 'eng', 'isOverlayRequired': 'true', 'scale': 'true', 'OCREngine': '2'},
            headers={'apikey': OCR_KEY}, timeout=15)
        data = r.json()
        print('OCR result:', data)
        
        debug_dir = r'C:\Users\bt398\Downloads\tiktok bot\debug'
        os.makedirs(debug_dir, exist_ok=True)
        with open(os.path.join(debug_dir, 'captcha_test5.png'), 'wb') as f:
            f.write(base64.b64decode(b64))
        print('Saved captcha_test5.png')
    else:
        print('Canvas returned null - image not loaded in canvas context')
        
        print('Trying element screenshot instead...')
        try:
            el = d.find_element('id', 'captcha-img')
            png = el.screenshot_as_png
            debug_dir = r'C:\Users\bt398\Downloads\tiktok bot\debug'
            os.makedirs(debug_dir, exist_ok=True)
            with open(os.path.join(debug_dir, 'captcha_screenshot5.png'), 'wb') as f:
                f.write(png)
            b64_ss = base64.b64encode(png).decode()
            r = requests.post('https://api.ocr.space/parse/image', 
                data={'base64Image': f'data:image/png;base64,{b64_ss}', 'language': 'eng', 'isOverlayRequired': 'true', 'scale': 'true', 'OCREngine': '2'},
                headers={'apikey': OCR_KEY}, timeout=15)
            print('Screenshot OCR:', r.json())
        except Exception as e:
            print(f'Screenshot failed: {e}')

finally:
    time.sleep(1)
    d.quit()
