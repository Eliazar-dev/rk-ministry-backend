"""Backend status page (/) and health check (/health/).

Plain Django views: no DRF, no throttling, no middleware, nothing shared with /api/.
Uptime = share of 5-minute slots (since the first check, up to the window) that had at least one OK heartbeat.
A heartbeat is written only when /health/ or / is opened (max once a minute), so point a free uptime
monitor (e.g. UptimeRobot, every 5 minutes) at /health/ to keep the numbers meaningful.
"""
import json
from datetime import timedelta

from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.utils import timezone

from .models import Heartbeat

SLOT = 300  # seconds
WINDOWS = {'24h': 1, '7d': 7, '30d': 30}


def _db_ok():
    try:
        with connection.cursor() as c:
            c.execute('SELECT 1')
        return True
    except Exception:
        return False


def _beat(ok):
    try:
        now = timezone.now()
        last = Heartbeat.objects.order_by('-at').first()
        if not last or (now - last.at).total_seconds() >= 60:
            Heartbeat.objects.create(at=now, ok=ok)
            Heartbeat.objects.filter(at__lt=now - timedelta(days=31)).delete()
    except Exception:
        pass


def _uptime():
    out = {}
    try:
        now = timezone.now()
        first = Heartbeat.objects.order_by('at').first()
        for label, days in WINDOWS.items():
            if not first:
                out[label] = None
                continue
            start = max(now - timedelta(days=days), first.at)
            total = max(1, int((now - start).total_seconds() // SLOT) + 1)
            slots = {int(h.timestamp() // SLOT) for h in
                     Heartbeat.objects.filter(ok=True, at__gte=start).values_list('at', flat=True)}
            out[label] = round(min(100.0, len(slots) * 100.0 / total), 2)
    except Exception:
        out = {k: None for k in WINDOWS}
    return out


def snapshot():
    ok = _db_ok()
    _beat(ok)
    return {
        'status': 'ok' if ok else 'degraded',
        'service': 'rk-ministry-api',
        'message': 'Backend running' if ok else 'Backend degraded: database error',
        'checked_at': timezone.localtime().strftime('%d %b %Y, %H:%M:%S'),
        'uptime': _uptime(),
    }


def health(request):
    if request.GET.get('detail'):
        data = snapshot()
        resp = JsonResponse(data, status=200 if data['status'] == 'ok' else 503)
    else:
        ok = _db_ok()
        _beat(ok)
        resp = JsonResponse({'status': 'ok' if ok else 'degraded', 'service': 'rk-ministry-api'}, status=200 if ok else 503)
    resp['Cache-Control'] = 'no-store'
    return resp


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Richard Kwanya Snr - Backend status</title><meta name="robots" content="noindex">
<style>
:root{--navy:#0a1a3f;--navy2:#13306b;--gold:#d4af37;--ok:#3ddc97;--warn:#ffb020}
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;color:#fff;
font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:radial-gradient(1200px 600px at 20% -10%,var(--navy2),var(--navy))}
.card{width:100%;max-width:520px;padding:32px 28px;border-radius:24px;background:rgba(255,255,255,.07);border:1px solid rgba(212,175,55,.35);
backdrop-filter:blur(14px);box-shadow:0 20px 60px rgba(0,0,0,.4);text-align:center}
.logo{width:84px;height:84px;border-radius:50%;object-fit:cover;border:3px solid var(--gold);background:#fff}
h1{font-size:1.15rem;margin:14px 0 2px;letter-spacing:.02em}h1 small{display:block;color:var(--gold);font-weight:600;font-size:.85rem;margin-top:2px}
.state{display:inline-flex;align-items:center;gap:12px;margin:22px 0 6px;font-size:1.25rem;font-weight:700}
.dot{width:14px;height:14px;border-radius:50%;background:var(--c);box-shadow:0 0 0 0 var(--c);animation:pulse 1.8s infinite}
.ok{--c:var(--ok)}.bad{--c:var(--warn)}.state.bad{color:var(--warn)}
@keyframes pulse{0%{box-shadow:0 0 0 0 color-mix(in srgb,var(--c) 70%,transparent)}70%{box-shadow:0 0 0 16px transparent}100%{box-shadow:0 0 0 0 transparent}}
.checked{color:#b9c4e0;font-size:.85rem;margin-bottom:20px}
.up{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.up div{padding:14px 6px;border-radius:14px;background:rgba(0,0,0,.22)}
.up b{display:block;font-size:1.3rem;color:var(--gold)}.up span{font-size:.75rem;color:#b9c4e0;text-transform:uppercase;letter-spacing:.08em}
.bar{margin-top:22px;display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;color:#b9c4e0;font-size:.85rem}
button{font:inherit;cursor:pointer;color:var(--navy);background:linear-gradient(135deg,#f3d97a,var(--gold));border:0;border-radius:999px;padding:7px 14px;font-weight:700}
button.ghost{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.35)}
@media (prefers-reduced-motion:reduce){.dot{animation:none}}
</style></head><body><main class="card">
<img class="logo" src="https://res.cloudinary.com/gfiqfk7x/image/upload/v1784123661/WhatsApp_Image_2026-07-15_at_4.53.19_PM_ktrbpg.jpg" alt="RK logo"
 onerror="if(!this.dataset.f){this.dataset.f=1;this.src='/static/monitoring/logo.jpg'}">
<h1>Richard Kwanya Snr<small>#Babawa &middot; Backend status</small></h1>
<div id="state" class="state __CLS__"><span class="dot __CLS__"></span><span id="msg">__MSG__</span></div>
<div class="checked">Last check: <span id="at">__AT__</span></div>
<div class="up"><div><b id="u24">__U24__</b><span>24 hours</span></div><div><b id="u7">__U7__</b><span>7 days</span></div><div><b id="u30">__U30__</b><span>30 days</span></div></div>
<div class="bar"><span id="count">Refreshing in 30s</span><button id="now">Refresh now</button><button id="pause" class="ghost">Pause</button></div>
</main>
<script>
(function(){var N=30,left=N,paused=false;
var $=function(i){return document.getElementById(i)};
function fmt(v){return v==null?'--':v+'%'}
function apply(d){$('msg').textContent=d.message;var c=d.status==='ok'?'ok':'bad';
$('state').className='state '+c;document.querySelector('.dot').className='dot '+c;
$('at').textContent=d.checked_at;$('u24').textContent=fmt(d.uptime['24h']);$('u7').textContent=fmt(d.uptime['7d']);$('u30').textContent=fmt(d.uptime['30d'])}
function load(){fetch('/health/?detail=1',{cache:'no-store'}).then(function(r){return r.json()}).then(apply).catch(function(){
apply({status:'bad',message:'Cannot reach the backend',checked_at:new Date().toLocaleTimeString(),uptime:{}})});left=N}
function tick(){if(paused||document.hidden){$('count').textContent=paused?'Paused':'Paused (tab hidden)';return}
left--;if(left<=0){load()}$('count').textContent='Refreshing in '+left+'s'}
$('now').onclick=load;$('pause').onclick=function(){paused=!paused;this.textContent=paused?'Resume':'Pause';tick()};
setInterval(tick,1000)})();
</script></body></html>"""


def status_page(request):
    d = snapshot()
    u = d['uptime']
    f = lambda v: '--' if v is None else f'{v}%'
    html = (PAGE.replace('__CLS__', 'ok' if d['status'] == 'ok' else 'bad').replace('__MSG__', d['message'])
            .replace('__AT__', d['checked_at']).replace('__U24__', f(u.get('24h')))
            .replace('__U7__', f(u.get('7d'))).replace('__U30__', f(u.get('30d'))))
    resp = HttpResponse(html)
    resp['Cache-Control'] = 'no-store'
    return resp
