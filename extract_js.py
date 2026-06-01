import requests
r = requests.get('https://zefoy.com/assets/53fbc84b11a13a7942a850361e5d7b49.js?v=5.6.1', timeout=15)
js = r.text

idx = js.find("'form')['on']")
print('=== FORM SUBMIT HANDLER ===')
print(js[idx-200:idx+2000])

print('\n\n=== CAPTCHA SUCCESS HANDLER ===')
idx2 = js.find("'data':_0x4ef7aa,'success'")
print(js[idx2-200:idx2+3000])

print('\n\n=== SECOND SUCCESS HANDLER (services) ===')
idx3 = js.find("'dataType':_0x4dc746(-0x197a+0x448+0xc19*0x2),'success'")
print(js[idx3-300:idx3+3000])
