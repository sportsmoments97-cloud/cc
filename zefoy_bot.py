import sys, io, time, re, json, requests, threading

class Unbuffered:
    def __init__(self, s): self.s = s
    def write(self, d): self.s.write(d); self.s.flush()
    def flush(self): self.s.flush()
    def __getattr__(self, a): return getattr(self.s, a)

sys.stdout = Unbuffered(sys.stdout)
sys.stderr = Unbuffered(sys.stderr)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

OCR_KEY = 'K84731687888957'
VIEWS_FORM_ACTION = 'c2VuZC9mb2xeb3dlcnNfdGlrdG9V'

VIEW_OPTIONS = {
    '100': 100,
    '1k': 1000,
    '10k': 10000,
    '100k': 100000,
    '1m': 1000000
}

VIEW_LABELS = {
    '100': '100 Views',
    '1k': '1,000 Views',
    '10k': '10,000 Views',
    '100k': '100,000 Views',
    '1m': '1,000,000 Views'
}

def ocr_captcha(b64):
    try:
        r = requests.post('https://api.ocr.space/parse/image',
            data={'base64Image': f'data:image/png;base64,{b64}', 'language': 'eng', 'OCREngine': 2},
            headers={'apikey': OCR_KEY}, timeout=15)
        data = r.json()
        if data.get('ParsedResults') and data['ParsedResults'][0].get('ParsedText'):
            text = data['ParsedResults'][0]['ParsedText'].strip()
            lines = data['ParsedResults'][0].get('TextOverlay', {}).get('Lines', [])
            word_count = sum(len(l.get('Words', [])) for l in lines)
            return text, word_count
    except Exception as e:
        print(f'OCR err: {e}')
    return None, 0

def get_count(url):
    try:
        from urllib.parse import unquote
        UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        r = requests.Session().get(url, headers={'User-Agent': UA, 'Accept': 'text/html'}, timeout=15)
        m = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.+?)</script>', r.text, re.DOTALL)
        if m:
            data = json.loads(unquote(m.group(1)))
            return data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {}).get('stats', {}).get('playCount', 0)
    except:
        pass
    return -1

class ZefoyBot:
    def __init__(self, video_url, target_views=1000, headless=True):
        self.video_url = video_url
        self.target_views = target_views
        self.headless = headless
        self.driver = None
        self.sent = 0
        self.total_views_sent = 0
        self.last_captcha_src = None
        self.starting_count = 0
        self.running = False
        self.status = 'idle'
        self.status_msg = ''
        self.last_error = ''
        self._lock = threading.Lock()
        self._start_time = 0

    def get_progress(self):
        with self._lock:
            current = get_count(self.video_url) if self.video_url else 0
            gained = max(0, current - self.starting_count)
            remaining = max(0, self.target_views - gained)
            elapsed = time.time() - self._start_time if self._start_time else 0
            return {
                'status': self.status,
                'message': self.status_msg,
                'last_error': self.last_error,
                'video_url': self.video_url,
                'target': self.target_views,
                'starting_count': self.starting_count,
                'current_count': current,
                'gained': gained,
                'remaining': remaining,
                'sends': self.sent,
                'elapsed_s': round(elapsed, 1),
                'progress_pct': min(100, round(gained / self.target_views * 100, 1)) if self.target_views > 0 else 0
            }

    def set_status(self, status, msg=''):
        with self._lock:
            self.status = status
            self.status_msg = msg

    def setup(self):
        options = Options()
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1366,768')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-notifications')
        if self.headless:
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
        options.add_experimental_option('prefs', {'profile.default_content_setting_values.notifications': 2})
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
        })
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': """
window._ajaxLog = [];
window._lastAjaxResponse = '';
window._lastAjaxUrl = '';
(function() {
    var origOpen = XMLHttpRequest.prototype.open;
    var origSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(method, url) {
        this._logUrl = url; this._logMethod = method;
        return origOpen.apply(this, arguments);
    };
    XMLHttpRequest.prototype.send = function(body) {
        var entry = {method: this._logMethod, url: this._logUrl, body: body, time: Date.now()};
        window._ajaxLog.push(entry);
        this.addEventListener('load', function() {
            entry.status = this.status;
            entry.response = this.responseText;
            window._lastAjaxResponse = this.responseText;
            window._lastAjaxUrl = this._logUrl || '';
        });
        return origSend.apply(this, arguments);
    };
})();
"""})

    def dismiss_alerts(self):
        for _ in range(5):
            try:
                WebDriverWait(self.driver, 1).until(EC.alert_is_present())
                self.driver.switch_to.alert.dismiss()
            except:
                break

    def remove_fc(self):
        self.driver.execute_script("""
            ['.fc-dialog-overlay','.fc-monetization-dialog-container','.fc-message-root',
             '[id*="fc-focus-trap"]','.fc-dialog-content','.fc-thank-you-snackbar'].forEach(function(s) {
                document.querySelectorAll(s).forEach(function(e) { e.remove(); });
            });
        """)

    def solve_captcha(self):
        self.set_status('captcha', 'Solving captcha...')
        for attempt in range(10):
            if not self.running:
                return False
            print(f'Captcha #{attempt+1}...')
            time.sleep(2)
            self.dismiss_alerts()

            src = self.driver.execute_script("var img=document.getElementById('captcha-img');return img?img.src:null;")
            if src == self.last_captcha_src:
                print(' Same captcha, refreshing...')
                self.last_captcha_src = None
                self.driver.refresh(); time.sleep(3); self.dismiss_alerts(); continue
            self.last_captcha_src = src

            b64 = self.driver.execute_script("""
                var img=document.getElementById('captcha-img');
                if(!img||!img.naturalWidth)return null;
                var c=document.createElement('canvas');c.width=img.naturalWidth;c.height=img.naturalHeight;
                c.getContext('2d').drawImage(img,0,0);return c.toDataURL('image/png').split(',')[1];
            """)
            if not b64:
                print(' No captcha, refreshing...')
                self.driver.refresh(); time.sleep(3); self.dismiss_alerts(); continue

            text, word_count = ocr_captcha(b64)
            if not text:
                print(' OCR empty')
                self.last_captcha_src = None
                self.driver.refresh(); time.sleep(3); self.dismiss_alerts(); continue

            cleaned = re.sub(r'[^a-zA-Z]', '', text).lower()
            print(f' OCR: "{text}" -> "{cleaned}" (words: {word_count})')

            if len(cleaned) < 4 or word_count > 3:
                print(' Bad OCR result')
                self.last_captcha_src = None
                self.driver.refresh(); time.sleep(3); self.dismiss_alerts(); continue

            self.remove_fc(); time.sleep(0.3)

            try:
                inp = self.driver.find_element(By.ID, 'captchatoken')
            except:
                inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="search"],input[type="text"]')
                inp = next((i for i in inputs if 'enter' in (i.get_attribute('placeholder') or '').lower() or 'word' in (i.get_attribute('placeholder') or '').lower()), inputs[0] if inputs else None)

            if not inp:
                print(' No input'); continue

            self.driver.execute_script("""
                var el=arguments[0];el.value=arguments[1];
                el.dispatchEvent(new Event('input',{bubbles:true}));
                el.dispatchEvent(new Event('change',{bubbles:true}));
            """, inp, cleaned)
            time.sleep(0.5)
            self.dismiss_alerts(); self.remove_fc()

            self.set_status('captcha', f'Submitting captcha answer: {cleaned}')
            print(' Submitting captcha...')
            self.driver.execute_script("$('form[action=\"/\"]').trigger('submit');")
            time.sleep(5)
            self.dismiss_alerts(); self.remove_fc(); time.sleep(0.5)

            body = ''
            try:
                body = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
            except:
                pass

            if 'views' in body and 'updated' in body:
                print(' UNLOCKED!')
                self.set_status('captcha', 'Captcha solved!')
                return True

            if 'wrong' in body or 'incorrect' in body:
                print(' Wrong captcha')
                self.last_captcha_src = None
                self.driver.refresh(); time.sleep(3); self.dismiss_alerts(); continue

            if 'enter the word' in body:
                print(' Still on captcha'); continue

            if 'unlock' in body or 'short ad' in body:
                print(' FC wall, refreshing...')
                self.remove_fc(); self.driver.refresh(); time.sleep(3)
                self.dismiss_alerts(); self.remove_fc(); time.sleep(0.5)
                try:
                    body2 = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
                except:
                    body2 = ''
                if 'views' in body2 and 'updated' in body2:
                    print(' UNLOCKED after refresh!')
                    self.set_status('captcha', 'Captcha solved!')
                    return True
                continue

            print(f' Unknown state, refreshing...')
            self.last_captcha_src = None
            self.driver.refresh(); time.sleep(3); self.dismiss_alerts()

        self.last_error = 'Captcha not solved in 10 attempts'
        return False

    def open_views_service(self):
        self.set_status('working', 'Opening Views service...')
        self.dismiss_alerts(); self.remove_fc(); time.sleep(0.5)

        btn = self.driver.execute_script("return document.querySelector('.t-views-button');")
        if not btn:
            print('No Views button!'); return False

        self.driver.execute_script("document.querySelector('.t-views-button').click();")
        time.sleep(1); self.dismiss_alerts(); self.remove_fc()

        menu_display = self.driver.execute_script("""
            var m=document.querySelector('.t-views-menu');
            return m?getComputedStyle(m).display:'N/A';
        """)
        if menu_display == 'none':
            self.driver.execute_script("var m=document.querySelector('.t-views-menu');if(m)m.setAttribute('style','display:block !important;');")
            time.sleep(1)

        return True

    def do_search(self):
        self.driver.execute_script('window._lastAjaxResponse="";window._lastAjaxUrl="";')

        self.driver.execute_script("""
            var inp=document.querySelector('.t-views-menu input');
            inp.value=arguments[0];
            inp.dispatchEvent(new Event('input',{bubbles:true}));
            inp.dispatchEvent(new Event('change',{bubbles:true}));
        """, self.video_url)
        time.sleep(0.5)

        self.driver.execute_script("$('form[action=\"" + VIEWS_FORM_ACTION + "\"]').trigger('submit');")

        for _ in range(10):
            time.sleep(0.5)
            resp = self.driver.execute_script('return window._lastAjaxResponse;')
            if resp:
                return True
        return False

    def parse_search_response(self):
        return self.driver.execute_script("""
            var r=document.getElementById('""" + VIEWS_FORM_ACTION + """');
            if(!r) return {type:'no_div'};

            var loginCd=document.getElementById('login-countdown');
            if(loginCd){
                var loginText=loginCd.textContent||'';
                var lm=loginText.match(/(\d+)\s*minute/g);
                var ls=loginText.match(/(\d+)\s*second/g);
                var total=0;
                if(lm){var mm=lm[0].match(/(\d+)/);if(mm)total+=parseInt(mm[1])*60;}
                if(ls){var ss=ls[0].match(/(\d+)/);if(ss)total+=parseInt(ss[1]);}
                if(total>0) return {type:'cooldown',seconds:total,rawText:loginText};
                var scripts2=r.querySelectorAll('script');
                for(var j=0;j<scripts2.length;j++){
                    var rm=scripts2[j].textContent.match(/remainingTimelogin\s*=\s*(\d+)/);
                    if(rm) return {type:'cooldown',seconds:parseInt(rm[1]),rawText:'remainingTimer'};
                }
            }

            var scripts=r.querySelectorAll('script');
            for(var i=0;i<scripts.length;i++){
                var s=scripts[i].textContent;
                if(s.indexOf('cdtm')!==-1 && s.indexOf('ltm')!==-1){
                    var m=s.match(/var ltm=(\\d+)/);
                    if(m) return {type:'cooldown',seconds:parseInt(m[1])};
                }
            }

            var wbtn=r.querySelector('.wbutton');
            if(wbtn){
                var form=wbtn.closest('form');
                var viewText=wbtn.textContent.replace(/[^0-9]/g,'');
                return {
                    type:'ready',
                    views:parseInt(viewText)||0,
                    formAction:form?form.getAttribute('action'):'',
                    formOnsubmit:form?form.getAttribute('onsubmit'):''
                };
            }

            return {type:'unknown',html:r.innerHTML.substring(0,300),text:r.textContent.substring(0,200)};
        """)

    def do_send(self):
        self.driver.execute_script('window._lastAjaxResponse="";window._lastAjaxUrl="";')
        count_before = get_count(self.video_url)

        self.driver.execute_script("""
            var r=document.getElementById('""" + VIEWS_FORM_ACTION + """');
            var form=r.querySelector('form[action=\"""" + VIEWS_FORM_ACTION + """\"]');
            if(form) {
                $(form).trigger('submit');
            }
        """)

        for _ in range(20):
            time.sleep(0.5)
            resp = self.driver.execute_script('return window._lastAjaxResponse;')
            if resp:
                return True

        count_after = get_count(self.video_url)
        if count_after > count_before:
            print(f' Send AJAX missed but views increased: {count_before} -> {count_after}')
            return True

        return False

    def check_target_reached(self):
        current = get_count(self.video_url)
        gained = max(0, current - self.starting_count)
        return gained >= self.target_views, current, gained

    def send_views_loop(self):
        if not self.open_views_service():
            self.last_error = 'Failed to open Views service'
            self.set_status('error', 'Failed to open Views service')
            return

        while self.running:
            try:
                self.dismiss_alerts(); self.remove_fc()

                reached, current, gained = self.check_target_reached()
                if reached:
                    self.set_status('complete', f'Target reached! {gained:,} / {self.target_views:,} views')
                    print(f'\n=== TARGET REACHED: {gained:,} / {self.target_views:,} ===')
                    return

                self.set_status('working', f'Searching... ({gained:,}/{self.target_views:,} views, {self.sent} sends)')

                ok = self.do_search()
                if not ok:
                    print('Search failed, retrying...')
                    time.sleep(3); continue

                time.sleep(1)
                result = self.parse_search_response()

                if result.get('type') == 'cooldown':
                    secs = result.get('seconds', 60)
                    secs = min(secs, 60)
                    self.set_status('cooldown', f'Waiting {secs}s cooldown... ({gained:,}/{self.target_views:,})')
                    print(f' Cooldown: {secs}s')
                    time.sleep(secs + 2)
                    continue

                if result.get('type') == 'ready':
                    views_this_send = result.get('views', 0)
                    print(f' READY! Will send ~{views_this_send} views')
                    self.set_status('working', f'Sending ~{views_this_send:,} views... ({gained:,}/{self.target_views:,})')

                    send_ok = self.do_send()
                    if send_ok:
                        self.sent += 1
                        self.total_views_sent += views_this_send
                        gained_after = max(0, get_count(self.video_url) - self.starting_count)
                        print(f' === SENT #{self.sent} (~{views_this_send:,} views) | Progress: {gained_after:,}/{self.target_views:,} ===')
                        self.set_status('working', f'Sent #{self.sent}! ({gained_after:,}/{self.target_views:,} views)')

                        time.sleep(2)
                        result2 = self.parse_search_response()
                        if result2.get('type') == 'cooldown':
                            secs = result2.get('seconds', 60)
                            secs = min(secs, 60)
                            self.set_status('cooldown', f'Sent! Waiting {secs}s... ({gained_after:,}/{self.target_views:,})')
                            time.sleep(secs + 2)
                        else:
                            time.sleep(30)
                    else:
                        print(' Send may have failed, waiting...')
                        self.set_status('working', 'Send failed, retrying...')
                        time.sleep(10)
                    continue

                raw = result.get('rawText', '') or result.get('text', '') or result.get('html', '')
                mins = re.search(r'(\d+)\s*minute', raw)
                secs_m = re.search(r'(\d+)\s*second', raw)
                total = 0
                if mins:
                    total += int(mins.group(1)) * 60
                if secs_m:
                    total += int(secs_m.group(1))
                if total > 0:
                    total = min(total, 60)
                    self.set_status('cooldown', f'Waiting {total}s... ({gained:,}/{self.target_views:,})')
                    print(f' Cooldown (parsed): {total}s')
                    time.sleep(total + 2)
                    continue

                rt = re.search(r'remainingTimelogin\s*=\s*(\d+)', raw)
                if rt:
                    secs = min(int(rt.group(1)), 60)
                    self.set_status('cooldown', f'Login cooldown {secs}s... ({gained:,}/{self.target_views:,})')
                    print(f' Login cooldown: {secs}s')
                    time.sleep(secs + 2)
                    continue

                print(f' Unknown: {str(result)[:200]}')
                self.set_status('working', f'Retrying... ({gained:,}/{self.target_views:,})')
                time.sleep(5)

            except Exception as e:
                print(f' Error: {str(e)[:100]}')
                self.last_error = str(e)[:120]
                self.set_status('error', f'Error: {str(e)[:80]}')
                time.sleep(3)
                self.remove_fc()

    def stop(self):
        self.running = False
        self.set_status('stopped', 'Stopped by user')

    def _timeout_watcher(self):
        last_sends = 0
        stalled_ticks = 0
        while self.running:
            time.sleep(15)
            if not self.running:
                return
            if self.sent > last_sends:
                last_sends = self.sent
                stalled_ticks = 0
                continue
            stalled_ticks += 1
            elapsed = time.time() - self._start_time if self._start_time else 0
            if self.sent == 0 and stalled_ticks >= 20:
                print(f'TIMEOUT: 5 min with no sends ({self.sent} sends, {elapsed:.0f}s)')
                self.last_error = f'Timed out after {elapsed:.0f}s with no sends'
                self.running = False
                return
            if self.sent > 0 and stalled_ticks >= 10:
                print(f'TIMEOUT: 2.5 min stalled after sends ({self.sent} sends, {elapsed:.0f}s)')
                self.last_error = f'Stalled after {self.sent} sends, {elapsed:.0f}s'
                self.running = False
                return

    def run(self):
        self.running = True
        self._start_time = time.time()
        self.starting_count = get_count(self.video_url)
        print(f'Starting view count: {self.starting_count:,} | Target: +{self.target_views:,}')
        self.set_status('starting', f'Starting bot... Target: +{self.target_views:,} views')

        threading.Thread(target=self._timeout_watcher, daemon=True).start()

        try:
            self.set_status('starting', 'Starting Chrome...')
            t0 = time.time()
            self.setup()
            print(f'Chrome started in {time.time()-t0:.1f}s')
            self.last_error = ''

            self.set_status('starting', 'Loading zefoy.com...')
            self.driver.get('https://zefoy.com')
            time.sleep(3)
            self.dismiss_alerts()

            self.set_status('captcha', 'Solving captcha...')
            if not self.solve_captcha():
                self.set_status('error', 'Failed to solve captcha')
                return

            self.send_views_loop()

        except Exception as e:
            print(f'Fatal: {e}')
            self.last_error = f'{type(e).__name__}: {str(e)[:120]}'
            self.set_status('error', f'Fatal: {str(e)[:80]}')
            import traceback
            traceback.print_exc()
        finally:
            final = get_count(self.video_url)
            gained = max(0, final - self.starting_count)
            print(f'\nViews: {self.starting_count:,} -> {final:,} (+{gained:,}, sends: {self.sent})')
            if self.status != 'complete':
                self.set_status('stopped', f'Finished. +{gained:,} views ({self.sent} sends)')
            time.sleep(2)
            try:
                self.driver.quit()
            except:
                pass

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='TikTok View Bot via Zefoy')
    parser.add_argument('url', help='TikTok video URL')
    parser.add_argument('-t', '--target', default='1k', choices=list(VIEW_OPTIONS.keys()),
                        help='Target views: 100, 1k, 10k, 100k, 1m (default: 1k)')
    parser.add_argument('--headless', action='store_true', default=False,
                        help='Run Chrome in headless mode')
    args = parser.parse_args()

    target = VIEW_OPTIONS[args.target]
    print(f'Target: {VIEW_LABELS[args.target]}')
    print(f'URL: {args.url}')
    print(f'Headless: {args.headless}')

    bot = ZefoyBot(args.url, target, headless=args.headless)
    try:
        bot.run()
    except KeyboardInterrupt:
        bot.stop()
        print('\nStopped!')
