import os, sys, io, base64, time, re, requests
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageFilter, ImageOps

OCR_KEY = 'K84731687888957'

def ocr(b64, engine=2, preprocess=None):
    try:
        r = requests.post('https://api.ocr.space/parse/image', 
            data={'base64Image': f'data:image/png;base64,{b64}', 'language': 'eng', 'isOverlayRequired': 'false', 'scale': 'true', 'OCREngine': str(engine)},
            headers={'apikey': OCR_KEY}, timeout=15)
        data = r.json()
        if data.get('ParsedResults') and data['ParsedResults'][0].get('ParsedText'):
            return data['ParsedResults'][0]['ParsedText'].strip()
    except Exception as e:
        print(f'  OCR err: {e}')
    return ''

def preprocess_image(b64, method):
    img = Image.open(io.BytesIO(base64.b64decode(b64)))
    if method == 'gray_thresh':
        img = img.convert('L')
        img = img.point(lambda x: 255 if x > 128 else 0, '1')
        img = img.convert('RGB')
    elif method == 'gray_otsu':
        img = img.convert('L')
        from PIL import ImageStat
        stat = ImageStat.Stat(img)
        mean = stat.mean[0]
        img = img.point(lambda x: 255 if x > mean else 0, '1')
        img = img.convert('RGB')
    elif method == 'invert':
        img = ImageOps.invert(img.convert('RGB'))
    elif method == 'gray':
        img = img.convert('L').convert('RGB')
    elif method == 'resize2x':
        w, h = img.size
        img = img.resize((w*2, h*2), Image.LANCZOS)
    elif method == 'resize3x':
        w, h = img.size
        img = img.resize((w*3, h*3), Image.LANCZOS)
    elif method == 'sharpen':
        img = img.convert('RGB').filter(ImageFilter.SHARPEN)
    elif method == 'gray_sharpen':
        img = img.convert('L').convert('RGB').filter(ImageFilter.SHARPEN)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()

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

    b64_natural = d.execute_script("""
        var img = document.getElementById('captcha-img');
        if (!img || !img.naturalWidth) return null;
        var canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        return canvas.toDataURL('image/png').split(',')[1];
    """)
    
    if not b64_natural:
        print('No captcha found')
    else:
        img = Image.open(io.BytesIO(base64.b64decode(b64_natural)))
        print(f'Natural size: {img.size}, mode: {img.mode}')
        
        methods = ['raw', 'gray', 'gray_thresh', 'gray_otsu', 'invert', 'resize2x', 'resize3x', 'sharpen', 'gray_sharpen']
        
        for method in methods:
            if method == 'raw':
                test_b64 = b64_natural
            else:
                try:
                    test_b64 = preprocess_image(b64_natural, method)
                except Exception as e:
                    print(f'{method}: preprocess err: {e}')
                    continue
            
            for engine in [2, 1]:
                result = ocr(test_b64, engine)
                cleaned = re.sub(r'[^a-zA-Z]', '', result).lower()
                print(f'{method:15s} eng{engine}: "{result:30s}" -> "{cleaned}"')

finally:
    time.sleep(1)
    d.quit()
