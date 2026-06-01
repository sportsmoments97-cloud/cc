import os, sys, io, threading, json, time, re, traceback

class Unbuffered:
    def __init__(self, s): self.s = s
    def write(self, d): self.s.write(d); self.s.flush()
    def flush(self): self.s.flush()
    def __getattr__(self, a): return getattr(self.s, a)

sys.stdout = Unbuffered(sys.stdout)
sys.stderr = Unbuffered(sys.stderr)

from flask import Flask, request, jsonify
app = Flask(__name__)

try:
    from zefoy_bot import ZefoyBot, VIEW_OPTIONS, VIEW_LABELS, get_count
    IMPORT_OK = True
    IMPORT_ERROR = None
except Exception as e:
    IMPORT_OK = False
    IMPORT_ERROR = str(e)
    traceback.print_exc()
    VIEW_OPTIONS = {'100': 100, '1k': 1000, '10k': 10000, '100k': 100000, '1m': 1000000}
    VIEW_LABELS = {'100': '100 Views', '1k': '1,000 Views', '10k': '10,000 Views', '100k': '100,000 Views', '1m': '1,000,000 Views'}

active_bot = None
bot_thread = None
bot_lock = threading.Lock()

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TikTok View Bot</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0a0a0a;--card:#141414;--card2:#1a1a1a;--border:#252525;--border2:#333;--text:#e5e5e5;--text2:#999;--accent:#ff2d55;--accent2:#ff6b8a;--green:#30d158;--blue:#0a84ff;--orange:#ff9f0a;--purple:#bf5af2;--pink:#ff375f}
body{background:var(--bg);color:var(--text);font-family:'Inter',-apple-system,sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.container{max-width:480px;width:100%}
.logo{text-align:center;margin-bottom:32px}
.logo-icon{width:64px;height:64px;background:linear-gradient(135deg,var(--accent),#ff6b8a);border-radius:18px;display:inline-flex;align-items:center;justify-content:center;font-size:28px;margin-bottom:12px;box-shadow:0 8px 32px rgba(255,45,85,0.3)}
.logo h1{font-size:24px;font-weight:800;letter-spacing:-0.5px}
.logo p{color:var(--text2);font-size:13px;margin-top:4px}
.input-group{margin-bottom:24px}
.input-group label{display:block;font-size:12px;font-weight:600;color:var(--text2);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px}
.url-input{width:100%;background:var(--card);border:1.5px solid var(--border);border-radius:12px;padding:14px 16px 14px 44px;color:var(--text);font-size:14px;font-family:inherit;outline:none;transition:all .2s}
.url-input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(255,45,85,0.15)}
.url-input::placeholder{color:#555}
.input-wrap{position:relative}
.input-wrap i{position:absolute;left:16px;top:50%;transform:translateY(-50%);color:#555;font-size:14px}
.view-options{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-bottom:24px}
.view-option{background:var(--card);border:1.5px solid var(--border);border-radius:12px;padding:16px 8px;text-align:center;cursor:pointer;transition:all .2s;user-select:none}
.view-option:hover{border-color:var(--border2);background:var(--card2);transform:translateY(-1px)}
.view-option.selected{border-color:var(--accent);background:rgba(255,45,85,0.08);box-shadow:0 0 0 3px rgba(255,45,85,0.1)}
.view-option .icon{font-size:20px;margin-bottom:6px}
.view-option .count{font-size:14px;font-weight:700}
.view-option .label{font-size:9px;color:var(--text2);margin-top:2px;text-transform:uppercase;letter-spacing:0.3px}
.view-option.selected .count{color:var(--accent)}
.btn{width:100%;padding:16px;border:none;border-radius:14px;font-size:16px;font-weight:700;font-family:inherit;cursor:pointer;transition:all .2s;text-transform:none;letter-spacing:-0.3px}
.btn-start{background:linear-gradient(135deg,var(--accent),#ff6b8a);color:#fff;box-shadow:0 4px 20px rgba(255,45,85,0.35)}
.btn-start:hover{transform:translateY(-1px);box-shadow:0 6px 28px rgba(255,45,85,0.45)}
.btn-start:active{transform:translateY(0)}
.btn-start:disabled{opacity:0.4;cursor:not-allowed;transform:none;box-shadow:none}
.btn-stop{background:var(--card);color:var(--accent);border:1.5px solid var(--accent);margin-top:10px}
.btn-stop:hover{background:rgba(255,45,85,0.08)}
.progress-section{margin-top:28px;display:none}
.progress-section.active{display:block}
.status-bar{background:var(--card);border:1.5px solid var(--border);border-radius:14px;padding:20px;margin-bottom:12px}
.status-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.status-badge{padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.3px}
.status-badge.working{background:rgba(10,132,255,0.15);color:var(--blue)}
.status-badge.captcha{background:rgba(191,90,242,0.15);color:var(--purple)}
.status-badge.cooldown{background:rgba(255,159,10,0.15);color:var(--orange)}
.status-badge.complete{background:rgba(48,209,88,0.15);color:var(--green)}
.status-badge.error{background:rgba(255,55,95,0.15);color:var(--pink)}
.status-badge.stopped{background:rgba(153,153,153,0.15);color:var(--text2)}
.status-message{font-size:13px;color:var(--text2);margin-bottom:16px}
.progress-track{width:100%;height:8px;background:var(--border);border-radius:4px;overflow:hidden}
.progress-fill{height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:4px;transition:width .8s ease;position:relative}
.progress-fill::after{content:'';position:absolute;top:0;left:0;right:0;bottom:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.2),transparent);animation:shimmer 2s infinite}
@keyframes shimmer{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}
.progress-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px}
.stat{text-align:center}
.stat-value{font-size:20px;font-weight:800;letter-spacing:-0.5px}
.stat-value.accent{color:var(--accent)}
.stat-value.green{color:var(--green)}
.stat-value.blue{color:var(--blue)}
.stat-label{font-size:10px;color:var(--text2);text-transform:uppercase;letter-spacing:0.3px;margin-top:2px}
.logs{background:var(--card);border:1.5px solid var(--border);border-radius:14px;padding:16px;max-height:200px;overflow-y:auto;font-family:'SF Mono',Monaco,monospace;font-size:11px;line-height:1.6;color:var(--text2)}
.logs::-webkit-scrollbar{width:4px}
.logs::-webkit-scrollbar-track{background:transparent}
.logs::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px}
.log-entry{padding:2px 0}
.log-entry.success{color:var(--green)}
.log-entry.error{color:var(--pink)}
.log-entry.info{color:var(--blue)}
.footer{text-align:center;margin-top:32px;color:#444;font-size:11px}
@media(max-width:520px){.view-options{grid-template-columns:repeat(3,1fr)}.progress-stats{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<div class="container">
<div class="logo">
<div class="logo-icon"><i class="fab fa-tiktok"></i></div>
<h1>TikTok View Bot</h1>
<p>Send views to any TikTok video</p>
</div>
<div class="input-group">
<label>Video URL</label>
<div class="input-wrap">
<i class="fas fa-link"></i>
<input type="url" class="url-input" id="urlInput" placeholder="https://www.tiktok.com/@user/video/123...">
</div>
</div>
<div class="input-group">
<label>View Count</label>
<div class="view-options" id="viewOptions">
<div class="view-option" data-target="100" onclick="selectOption(this)">
<div class="icon"><i class="fas fa-eye"></i></div>
<div class="count">100</div>
<div class="label">Quick</div>
</div>
<div class="view-option selected" data-target="1k" onclick="selectOption(this)">
<div class="icon"><i class="fas fa-fire"></i></div>
<div class="count">1K</div>
<div class="label">Popular</div>
</div>
<div class="view-option" data-target="10k" onclick="selectOption(this)">
<div class="icon"><i class="fas fa-bolt"></i></div>
<div class="count">10K</div>
<div class="label">Viral</div>
</div>
<div class="view-option" data-target="100k" onclick="selectOption(this)">
<div class="icon"><i class="fas fa-rocket"></i></div>
<div class="count">100K</div>
<div class="label">Mega</div>
</div>
<div class="view-option" data-target="1m" onclick="selectOption(this)">
<div class="icon"><i class="fas fa-crown"></i></div>
<div class="count">1M</div>
<div class="label">Legend</div>
</div>
</div>
</div>
<button class="btn btn-start" id="startBtn" onclick="startBot()">
<i class="fas fa-play"></i>&nbsp; Start Bot
</button>
<button class="btn btn-stop" id="stopBtn" onclick="stopBot()" style="display:none">
<i class="fas fa-stop"></i>&nbsp; Stop Bot
</button>
<div class="progress-section" id="progressSection">
<div class="status-bar">
<div class="status-header">
<span style="font-size:14px;font-weight:600">Progress</span>
<span class="status-badge working" id="statusBadge">Working</span>
</div>
<div class="status-message" id="statusMessage">Starting...</div>
<div class="progress-track">
<div class="progress-fill" id="progressFill" style="width:0%"></div>
</div>
<div class="progress-stats">
<div class="stat">
<div class="stat-value accent" id="gainedStat">0</div>
<div class="stat-label">Gained</div>
</div>
<div class="stat">
<div class="stat-value green" id="targetStat">1,000</div>
<div class="stat-label">Target</div>
</div>
<div class="stat">
<div class="stat-value blue" id="sendsStat">0</div>
<div class="stat-label">Sends</div>
</div>
</div>
</div>
<div class="logs" id="logBox"></div>
</div>
<div class="footer">Powered by Zefoy &bull; For educational purposes only</div>
</div>
<script>
let selectedTarget = '1k';
let pollInterval = null;
let running = false;
const targetLabels = {100:'100','1k':'1,000','10k':'10,000','100k':'100,000','1m':'1,000,000'};
function selectOption(el) {
    document.querySelectorAll('.view-option').forEach(o => o.classList.remove('selected'));
    el.classList.add('selected');
    selectedTarget = el.dataset.target;
    document.getElementById('targetStat').textContent = targetLabels[selectedTarget];
}
function addLog(msg, cls) {
    const box = document.getElementById('logBox');
    const d = document.createElement('div');
    d.className = 'log-entry' + (cls ? ' ' + cls : '');
    const now = new Date();
    d.textContent = '[' + now.getHours().toString().padStart(2,'0') + ':' + now.getMinutes().toString().padStart(2,'0') + ':' + now.getSeconds().toString().padStart(2,'0') + '] ' + msg;
    box.appendChild(d);
    box.scrollTop = box.scrollHeight;
}
async function startBot() {
    const url = document.getElementById('urlInput').value.trim();
    if (!url) { alert('Enter a TikTok video URL'); return; }
    document.getElementById('startBtn').disabled = true;
    document.getElementById('startBtn').innerHTML = '<i class="fas fa-spinner fa-spin"></i>&nbsp; Starting...';
    document.getElementById('stopBtn').style.display = '';
    document.getElementById('progressSection').classList.add('active');
    running = true;
    addLog('Starting bot...', 'info');
    try {
        const res = await fetch('/api/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url, target: selectedTarget})
        });
        const data = await res.json();
        if (!res.ok) {
            addLog('Error: ' + data.error, 'error');
            resetUI();
            return;
        }
        addLog('Target: +' + targetLabels[selectedTarget] + ' views', 'info');
        startPolling();
    } catch(e) {
        addLog('Connection error: ' + e.message, 'error');
        resetUI();
    }
}
async function stopBot() {
    try {
        await fetch('/api/stop', {method: 'POST'});
        addLog('Stopping bot...', 'info');
    } catch(e) {}
    running = false;
    resetUI();
}
function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(async () => {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            updateUI(data);
            if (['complete','stopped','error','idle'].includes(data.status)) {
                clearInterval(pollInterval);
                running = false;
                resetUI();
            }
        } catch(e) {}
    }, 2000);
}
function updateUI(data) {
    const badge = document.getElementById('statusBadge');
    const msg = document.getElementById('statusMessage');
    const fill = document.getElementById('progressFill');
    const gained = document.getElementById('gainedStat');
    const sends = document.getElementById('sendsStat');
    badge.className = 'status-badge ' + data.status;
    badge.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
    msg.textContent = data.message || '';
    const pct = data.progress_pct || 0;
    fill.style.width = pct + '%';
    gained.textContent = (data.gained || 0).toLocaleString();
    sends.textContent = data.sends || 0;
    if (data.status === 'working') addLog('Send #' + data.sends + ' \u2014 ' + (data.gained || 0).toLocaleString() + '/' + (data.target || 0).toLocaleString(), 'success');
    else if (data.status === 'cooldown') addLog(data.message, 'info');
    else if (data.status === 'captcha') addLog('Solving captcha...', 'info');
    else if (data.status === 'error') addLog(data.message, 'error');
    else if (data.status === 'complete') addLog('Target reached!', 'success');
}
function resetUI() {
    document.getElementById('startBtn').disabled = false;
    document.getElementById('startBtn').innerHTML = '<i class="fas fa-play"></i>&nbsp; Start Bot';
    document.getElementById('stopBtn').style.display = 'none';
}
document.getElementById('targetStat').textContent = targetLabels[selectedTarget];
document.getElementById('urlInput').addEventListener('paste', function(e) {
    setTimeout(function() {
        const v = this.value.trim();
        if (v && !v.startsWith('http')) this.value = 'https://' + v;
    }.bind(this), 50);
});
</script>
</body>
</html>'''

@app.route('/')
def index():
    return HTML

@app.route('/api/health')
def health():
    chrome_test = _test_chrome_startup()
    return jsonify({
        'import_ok': IMPORT_OK,
        'import_error': IMPORT_ERROR,
        'chrome_version': _get_chrome_version(),
        'chromedriver_version': _get_chromedriver_version(),
        'chrome_startup_test': chrome_test
    })

def _get_chrome_version():
    try:
        import subprocess
        r = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True, timeout=5)
        return r.stdout.strip()
    except:
        return 'not found'

def _get_chromedriver_version():
    try:
        import subprocess
        r = subprocess.run(['chromedriver', '--version'], capture_output=True, text=True, timeout=5)
        return r.stdout.strip()
    except:
        return 'not found'

def _test_chrome_startup():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        opts = Options()
        opts.add_argument('--headless=new')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--disable-software-rasterizer')
        opts.add_argument('--window-size=800,600')
        d = webdriver.Chrome(options=opts)
        d.get('data:text/html,<h1>OK</h1>')
        title = d.title
        d.quit()
        return {'ok': True, 'title': title}
    except Exception as e:
        return {'ok': False, 'error': str(e)[:200]}

@app.route('/api/start', methods=['POST'])
def start_bot():
    global active_bot, bot_thread

    if not IMPORT_OK:
        return jsonify({'error': f'Import failed: {IMPORT_ERROR}'}), 500

    data = request.get_json() or {}
    url = data.get('url', '').strip()
    target_key = data.get('target', '1k')

    if not url:
        return jsonify({'error': 'Video URL required'}), 400

    if not re.match(r'https?://(www\.)?tiktok\.com/@.+?/video/\d+', url):
        return jsonify({'error': 'Invalid TikTok video URL'}), 400

    if target_key not in VIEW_OPTIONS:
        return jsonify({'error': 'Invalid target'}), 400

    with bot_lock:
        if active_bot and active_bot.running:
            return jsonify({'error': 'Bot already running'}), 409

        target = VIEW_OPTIONS[target_key]
        active_bot = ZefoyBot(url, target, headless=True)

        def run_bot():
            try:
                active_bot.run()
            except Exception as e:
                print(f'Bot thread error: {e}')
                traceback.print_exc()
                active_bot.set_status('error', f'Bot crashed: {str(e)[:80]}')

        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()

    return jsonify({'status': 'started', 'target': target, 'label': VIEW_LABELS[target_key]})

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    global active_bot
    with bot_lock:
        if active_bot and active_bot.running:
            active_bot.stop()
            return jsonify({'status': 'stopping'})
        return jsonify({'status': 'not_running'})

@app.route('/api/status')
def get_status():
    global active_bot
    with bot_lock:
        if not active_bot:
            return jsonify({'status': 'idle', 'message': 'No bot running'})
        return jsonify(active_bot.get_progress())

@app.route('/api/count')
def get_view_count():
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL required'}), 400
    count = get_count(url)
    return jsonify({'count': count})

@app.route('/api/options')
def get_options():
    return jsonify({'options': {k: {'value': v, 'label': VIEW_LABELS[k]} for k, v in VIEW_OPTIONS.items()}})

@app.errorhandler(Exception)
def handle_error(e):
    traceback.print_exc()
    return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
