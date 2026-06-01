import os, sys, io, base64, time, re, requests
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from PIL import Image

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
    
    img = d.find_element(By.ID, 'captcha-img')
    src = img.get_attribute('src')
    print(f'SRC: {src}')
    
    cookies = {c['name']: c['value'] for c in d.get_cookies()}
    print(f'Cookies: {cookies}')
    
    session = requests.Session()
    r = session.get(src, cookies=cookies, timeout=15)
    print(f'Download status: {r.status_code}, size: {len(r.content)} bytes')
    print(f'Content-Type: {r.headers.get("Content-Type", "unknown")}')
    
    debug_dir = r'C:\Users\bt398\Downloads\tiktok bot\debug'
    os.makedirs(debug_dir, exist_ok=True)
    
    with open(os.path.join(debug_dir, 'captcha_raw.png'), 'wb') as f:
        f.write(r.content)
    print('Saved captcha_raw.png')
    
    img_data = d.execute_script("""
        var img = document.getElementById('captcha-img');
        var canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight);
        return canvas.toDataURL('image/png').split(',')[1];
    """)
    
    with open(os.path.join(debug_dir, 'captcha_canvas.png'), 'wb') as f:
        f.write(base64.b64decode(img_data))
    print('Saved captcha_canvas.png (via canvas, natural size)')
    
    png = img.screenshot_as_png
    with open(os.path.join(debug_dir, 'captcha_screenshot.png'), 'wb') as f:
        f.write(png)
    print('Saved captcha_screenshot.png (element screenshot)')
    
    pil_img = Image.open(io.BytesIO(png))
    print(f'Screenshot size: {pil_img.size}')
    
    pil_raw = Image.open(io.BytesIO(r.content))
    print(f'Raw download size: {pil_raw.size}')
    
    pil_canvas = Image.open(io.BytesIO(base64.b64decode(img_data)))
    print(f'Canvas size: {pil_canvas.size}')
    
    captcha_b64_raw = base64.b64encode(r.content).decode()
    print(f'\nRaw image base64 length: {len(captcha_b64_raw)}')
    
    ocr_result = requests.post('https://api.ocr.space/parse/image', 
        data={'base64Image': f'data:image/png;base64,{captcha_b64_raw}', 'language': 'eng', 'isOverlayRequired': 'false', 'scale': 'true', 'OCREngine': '2'},
        headers={'apikey': 'K84731687888957'}, timeout=15)
    print(f'OCR raw: {ocr_result.json()}')
    
    captcha_b64_canvas = img_data
    ocr_result2 = requests.post('https://api.ocr.space/parse/image', 
        data={'base64Image': f'data:image/png;base64,{captcha_b64_canvas}', 'language': 'eng', 'isOverlayRequired': 'false', 'scale': 'true', 'OCREngine': '2'},
        headers={'apikey': 'K84731687888957'}, timeout=15)
    print(f'OCR canvas: {ocr_result2.json()}')

finally:
    time.sleep(2)
    d.quit()
