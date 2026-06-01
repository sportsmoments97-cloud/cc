import os, sys, io, base64, time, re
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
    
    captcha_img = d.find_element(By.ID, 'captcha-img')
    src = captcha_img.get_attribute('src')
    print(f'captcha-img src: "{src}"')
    print(f'captcha-img size: {captcha_img.size}')
    print(f'captcha-img location: {captcha_img.location}')
    
    parent = captcha_img.find_element(By.XPATH, '..')
    print(f'parent tag: {parent.tag_name}, class: {parent.get_attribute("class")}')
    print(f'parent size: {parent.size}')
    print(f'parent HTML: {parent.get_attribute("outerHTML")[:300]}')
    
    grandparent = parent.find_element(By.XPATH, '..')
    print(f'grandparent tag: {grandparent.tag_name}, class: {grandparent.get_attribute("class")}')
    print(f'grandparent size: {grandparent.size}')
    
    all_imgs = d.find_elements(By.TAG_NAME, 'img')
    print(f'\nAll images ({len(all_imgs)}):')
    for i, img in enumerate(all_imgs):
        s = img.size
        l = img.location
        src = img.get_attribute('src') or ''
        iid = img.get_attribute('id') or ''
        cls = img.get_attribute('class') or ''
        disp = img.is_displayed()
        print(f'  #{i}: id="{iid}" class="{cls}" size={s} loc={l} displayed={disp} src="{src[:80]}"')
    
    os.makedirs(r'C:\Users\bt398\Downloads\tiktok bot\debug', exist_ok=True)
    
    for i, img in enumerate(all_imgs):
        if img.is_displayed() and img.size['width'] > 50:
            png = img.screenshot_as_png
            path = os.path.join(r'C:\Users\bt398\Downloads\tiktok bot\debug', f'img_{i}.png')
            with open(path, 'wb') as f:
                f.write(png)
            print(f'  Saved img_{i}.png ({img.size["width"]}x{img.size["height"]})')
    
    captcha_area = d.execute_script("""
        var img = document.getElementById('captcha-img');
        if (!img) return null;
        
        var rect = img.getBoundingClientRect();
        var info = {
            top: rect.top,
            left: rect.left,
            width: rect.width,
            height: rect.height,
            naturalWidth: img.naturalWidth,
            naturalHeight: img.naturalHeight,
            src: img.src,
            parentHTML: img.parentElement.outerHTML.substring(0, 500),
            children: img.children.length
        };
        
        var container = img.closest('.wrapper-capth') || img.closest('div[class*="captcha"]');
        if (container) {
            var cRect = container.getBoundingClientRect();
            info.containerClass = container.className;
            info.containerWidth = cRect.width;
            info.containerHeight = cRect.height;
            info.containerTop = cRect.top;
            info.containerLeft = cRect.left;
        }
        
        return info;
    """)
    print(f'\nCaptcha details: {captcha_area}')
    
    d.save_screenshot(os.path.join(r'C:\Users\bt398\Downloads\tiktok bot\debug', 'full_page.png'))

finally:
    time.sleep(2)
    d.quit()
