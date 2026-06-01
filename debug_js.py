import os, sys, io, base64, time, re, json, requests
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
    time.sleep(5)
    for _ in range(5):
        try:
            WebDriverWait(d, 1).until(EC.alert_is_present())
            d.switch_to.alert.dismiss()
        except:
            break
    time.sleep(2)

    print('=== ALL SCRIPT TAGS ===')
    scripts = d.execute_script("""
        var scripts = document.querySelectorAll('script');
        var result = [];
        scripts.forEach(function(s) {
            if (s.src) result.push({src: s.src, inline: false});
            else if (s.textContent.trim().length > 0 && s.textContent.trim().length < 5000) 
                result.push({inline: true, text: s.textContent.trim()});
        });
        return result;
    """)
    for s in scripts:
        if s.get('src'):
            print(f'  External: {s["src"]}')
        elif s.get('text'):
            print(f'  Inline ({len(s["text"])} chars): {s["text"][:300]}...')

    print('\n=== FORM DETAILS ===')
    form_info = d.execute_script("""
        var form = document.querySelector('form[action="/"]');
        if (!form) return 'no form';
        var inputs = form.querySelectorAll('input');
        var result = {action: form.action, method: form.method, id: form.id, inputs: []};
        inputs.forEach(function(inp) {
            result.inputs.push({
                name: inp.name, type: inp.type, id: inp.id, 
                value: inp.value.substring(0, 50), 
                placeholder: inp.placeholder,
                hidden: inp.type === 'hidden'
            });
        });
        return result;
    """)
    print(json.dumps(form_info, indent=2))

    print('\n=== CAPTCHA SUBMIT HANDLERS ===')
    handlers = d.execute_script("""
        var form = document.querySelector('form[action="/"]');
        if (!form) return 'no form';
        var result = {};
        result.onsubmit = form.onsubmit ? form.onsubmit.toString() : null;
        result.jquery_events = (typeof $ !== 'undefined' && $._data) ? 
            ($._data(form, 'events') || 'none') : 'no jquery';
        var img = document.getElementById('captcha-img');
        if (img) {
            result.captcha_onload = img.onload ? img.onload.toString() : null;
        }
        return result;
    """)
    print(json.dumps(handlers, indent=2, default=str))

    print('\n=== LOOKING FOR AJAX SUBMIT CODE ===')
    ajax_code = d.execute_script("""
        var scripts = document.querySelectorAll('script');
        var code = '';
        scripts.forEach(function(s) {
            code += s.textContent + '\\n';
        });
        var patterns = ['ajax', 'submit', 'captcha', 'success', 'pfsauvvdgrhjqrl', 'POST'];
        var results = {};
        patterns.forEach(function(p) {
            var idx = code.indexOf(p);
            if (idx >= 0) {
                var start = Math.max(0, idx - 100);
                var end = Math.min(code.length, idx + 300);
                results[p] = code.substring(start, end);
            }
        });
        return results;
    """)
    for key, val in ajax_code.items():
        print(f'\n--- {key} ---')
        print(val[:500])

    print('\n=== MAIN CONTAINER CONTENT ===')
    main = d.execute_script("""
        var containers = document.querySelectorAll('.container, .main, #main, main, [class*="content"], [class*="body"]');
        var result = [];
        containers.forEach(function(c) {
            if (c.children.length > 0) {
                result.push({tag: c.tagName, class: c.className, id: c.id, 
                    childCount: c.children.length, text: c.textContent.substring(0, 200)});
            }
        });
        return result.slice(0, 5);
    """)
    for m in main:
        print(f'  {m["tag"]}.{m["class"]}: {m["text"][:100]}')

finally:
    time.sleep(2)
    d.quit()
