import os, sys, io, requests, re
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
})

print('Fetching zefoy.com...')
r = session.get('https://zefoy.com', timeout=15)
print(f'Status: {r.status_code}')
print(f'Cookies: {dict(session.cookies)}')

html = r.text

with open(r'C:\Users\bt398\Downloads\tiktok bot\debug\zefoy_http.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Saved HTML')

print('\n=== Looking for captcha patterns ===')
patterns = {
    'img src': re.findall(r'img[^>]*src="([^"]*)"', html),
    'input hidden': re.findall(r'<input type="hidden" name="([^"]*)"', html),
    'input text': re.findall(r'<input[^>]*type="text"[^>]*name="([^"]*)"', html),
    'captcha in src': re.findall(r'img[^>]*src="([^"]*(?:captcha|CAPTCHA|rand)[^"]*)"', html, re.IGNORECASE),
    'form action': re.findall(r'<form[^>]*action="([^"]*)"', html),
    'all img': re.findall(r'<img[^>]*>', html),
    'all input': re.findall(r'<input[^>]*>', html),
    'all form': re.findall(r'<form[^>]*>', html),
    'remove-spaces': re.findall(r'remove-spaces[^"]*name="([^"]*)"', html),
    'oninput': re.findall(r'oninput="this\.value[^"]*"[^>]*name="([^"]*)"', html),
    'placeholder': re.findall(r'placeholder="([^"]*)"', html),
}

for name, matches in patterns.items():
    print(f'\n{name}: {matches[:10]}')

print('\n=== First 3000 chars of HTML ===')
print(html[:3000])
