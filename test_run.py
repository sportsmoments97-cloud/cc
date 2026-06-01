from zefoy_bot import ZefoyBot
import threading, time

bot = ZefoyBot('https://www.tiktok.com/@guarddiszen1/video/7645679725960056095', target_views=100, headless=False)
t = threading.Thread(target=bot.run, daemon=True)
t.start()

for i in range(36):
    time.sleep(10)
    p = bot.get_progress()
    print(f'{(i+1)*10}s | status={p["status"]} | msg={p["message"][:60]} | sends={p["sends"]} | gained={p["gained"]} | err={p.get("last_error","")}')
    if p['status'] in ('complete', 'stopped', 'error', 'idle'):
        break

bot.stop()
p = bot.get_progress()
print(f'\nFINAL: status={p["status"]} gained={p["gained"]} sends={p["sends"]} err={p.get("last_error","")}')
