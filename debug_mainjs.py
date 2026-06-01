import os, sys, io, base64, time, re, json, requests
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

r = requests.get('https://zefoy.com/assets/53fbc84b11a13a7942a850361e5d7b49.js?v=5.6.1', timeout=15)
print(f'Status: {r.status_code}, Length: {len(r.text)}')
print(r.text[:5000])
