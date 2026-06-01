import requests, re, json, time, random, string
from base64 import b64encode
from io import BytesIO

class ZefoyBot:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'authority': 'zefoy.com',
            'origin': 'https://zefoy.com',
            'referer': 'https://zefoy.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
        })
        self.captcha_token = None
        self.token_answer_name = None
        
    def get_captcha(self):
        print('Fetching zefoy.com homepage...')
        r = self.session.get('https://zefoy.com', timeout=15)
        print(f'Status: {r.status_code}, Length: {len(r.text)}')
        
        source = r.text.replace('&amp;', '&')
        
        captcha_tokens = re.findall(r'<input type="hidden" name="(.*)">', source)
        if 'token' in captcha_tokens:
            captcha_tokens.remove('token')
        
        captcha_imgs = re.findall(r'img src="([^"]*)"', source)
        token_answer = re.findall(r'type="text" name="(.*)" oninput="this.value', source)
        
        print(f'Captcha tokens: {captcha_tokens}')
        print(f'Captcha images: {captcha_imgs}')
        print(f'Token answer field: {token_answer}')
        
        if captcha_imgs:
            img_url = 'https://zefoy.com' + captcha_imgs[0] if captcha_imgs[0].startswith('/') else captcha_imgs[0]
            img_resp = self.session.get(img_url, timeout=10)
            print(f'Captcha image: {len(img_resp.content)} bytes')
            
            with open(r'C:\Users\bt398\Downloads\tiktok bot\captcha.png', 'wb') as f:
                f.write(img_resp.content)
            print('Saved captcha.png')
        
        return captcha_tokens, token_answer
    
    def check_services(self):
        r = self.session.get('https://zefoy.com', timeout=15)
        source = r.text
        
        services = {
            'views': 'Views' in source or 'views' in source.lower(),
            'followers': 'Followers' in source,
            'hearts': 'Hearts' in source or 'Likes' in source,
            'shares': 'Shares' in source,
            'favorites': 'Favorites' in source,
        }
        
        for name, available in services.items():
            status = 'AVAILABLE' if available else 'OFFLINE'
            print(f'  {name}: {status}')
        
        view_match = re.search(r'(send[_\\]views[_\\]tiktok[^"]*)', source)
        if view_match:
            print(f'View service endpoint: {view_match.group(1)}')
        
        buttons = re.findall(r'<button[^>]*class="[^"]*btn[^"]*"[^>]*>([^<]+)</button>', source)
        print(f'Buttons found: {buttons}')
        
        return services

try:
    bot = ZefoyBot()
    tokens, answer_field = bot.get_captcha()
    print()
    bot.check_services()
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
