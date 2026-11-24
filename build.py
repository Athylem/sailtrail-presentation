"""Assemble la présentation Sail Trail en une page web autonome (index.html).

Sources : source/deck.json (ordre des diapos), source/deck.css (thème),
source/slides/*.html (une diapo par fichier), assets/ (logos SVG, photos).
Usage : python build.py
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / 'source'

# Images de l'éditeur Claude (/_blob/...) -> fichiers locaux
BLOBS = {
    'c772257ba3c8bbaa75969465b1bebf6a': 'assets/logo_navy.svg',
    '4561469edd78ca4f36f27c21972767bf': 'assets/logo_navy.svg',
    '46f67d414f74be551db803212e176d41': 'assets/logo_yellow.svg',
    'e7a335a6233392955f10a7d6f9e2db13': 'assets/nomade.jpg',
    'bc4260e57eff296de207694f5f6bcd1a': 'assets/sailor.jpg',
    '774c939cbd9d971c518f2a1dd982344e': 'assets/site_nomade.png',
    '9906218e5c19921c0dee5a4943bd6acb': 'assets/jordan.jpg',
}

PLAYER_CSS = r"""
html, body { margin: 0; height: 100%; background: #08111F; overflow: hidden; }
#stage { position: absolute; left: 50%; top: 50%; width: 1920px; height: 1080px; transform-origin: 0 0; overflow: hidden; background: #0E1B33; }
#stage > section { position: absolute; inset: 0; width: 1920px; height: 1080px; display: none; overflow: hidden; }
#stage > section.active { display: flex; }
#stage > section.enter { animation: deck-push 700ms cubic-bezier(.16, 1, .3, 1) both; }
#stage > section.enter-back { animation: deck-push-back 700ms cubic-bezier(.16, 1, .3, 1) both; }
@keyframes deck-push { from { transform: translateX(14%); opacity: 0; } to { transform: none; opacity: 1; } }
@keyframes deck-push-back { from { transform: translateX(-14%); opacity: 0; } to { transform: none; opacity: 1; } }
section::after { content: attr(data-n) !important; }
section.cover::after { content: none !important; }
aside { display: none; }
p, h1, h2, h3 { margin: 0; }
th, td { text-align: left; padding: 10px 12px; vertical-align: top; }
th { color: var(--navy); border-bottom: 3px solid var(--yellow); }
td { border-bottom: 1px solid var(--line); }
x-shape { display: inline-block; }
x-shape[kind="arrow-right"] { clip-path: polygon(0 32%, 62% 32%, 62% 0, 100% 50%, 62% 100%, 62% 68%, 0 68%); }
#notes { position: fixed; left: 0; right: 0; bottom: 0; max-height: 40vh; overflow: auto; background: rgba(8, 17, 31, .94); color: #FFFCF3; font: 18px/1.5 'DM Sans', Arial, sans-serif; padding: 18px 28px; display: none; z-index: 10; }
#notes.on { display: block; }
#hint { position: fixed; right: 16px; bottom: 12px; font: 13px/1.4 'DM Sans', Arial, sans-serif; color: #7F8FAA; z-index: 9; transition: opacity .6s; }
#prog { position: fixed; left: 0; bottom: 0; height: 4px; background: #F6C21B; z-index: 9; transition: width .4s; }
@media (prefers-reduced-motion: reduce) { #stage > section.enter, #stage > section.enter-back { animation: none; } }
"""

PLAYER_JS = r"""
(() => {
  const stage = document.getElementById('stage');
  const slides = [...stage.querySelectorAll(':scope > section')];
  const notes = document.getElementById('notes');
  const prog = document.getElementById('prog');
  let cur = 0, step = 0;

  const frags = s => {
    const f = [...s.querySelectorAll('.fragment')];
    return f.map((el, i) => ({ el, k: el.dataset.fragmentIndex !== undefined ? +el.dataset.fragmentIndex : 1000 + i }))
            .sort((a, b) => a.k - b.k);
  };
  // regroupe les fragments qui partagent le même index
  const groups = s => {
    const out = [];
    frags(s).forEach(f => { const g = out.find(x => x.k === f.k); g ? g.els.push(f.el) : out.push({ k: f.k, els: [f.el] }); });
    return out;
  };

  function show(i, dir, atEnd) {
    slides.forEach(s => s.classList.remove('active', 'enter', 'enter-back'));
    const s = slides[i];
    const g = groups(s);
    step = atEnd ? g.length : 0;
    g.forEach((grp, n) => grp.els.forEach(el => el.classList.toggle('visible', n < step)));
    void s.offsetWidth;
    s.classList.add('active');
    if (dir) s.classList.add(dir > 0 ? 'enter' : 'enter-back');
    cur = i;
    notes.textContent = s.querySelector('aside')?.textContent || '';
    prog.style.width = ((i + 1) / slides.length * 100) + '%';
    history.replaceState(null, '', '#' + (i + 1));
  }

  function next() {
    const g = groups(slides[cur]);
    if (step < g.length) { g[step].els.forEach(el => el.classList.add('visible')); step++; return; }
    if (cur < slides.length - 1) show(cur + 1, 1);
  }
  function prev() {
    const g = groups(slides[cur]);
    if (step > 0) { step--; g[step].els.forEach(el => el.classList.remove('visible')); return; }
    if (cur > 0) show(cur - 1, -1, true);
  }

  function fit() {
    const k = Math.min(innerWidth / 1920, innerHeight / 1080);
    stage.style.transform = `scale(${k}) translate(-50%, -50%)`;
  }
  addEventListener('resize', fit); fit();

  addEventListener('keydown', e => {
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].includes(e.key)) { e.preventDefault(); next(); }
    else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(e.key)) { e.preventDefault(); prev(); }
    else if (e.key === 'Home') show(0);
    else if (e.key === 'End') show(slides.length - 1, 0, true);
    else if (e.key === 'n' || e.key === 'N') notes.classList.toggle('on');
    else if (e.key === 'f' || e.key === 'F') {
      try { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen(); } catch (_) {}
    }
  });
  document.addEventListener('click', e => { if (!notes.contains(e.target)) (e.clientX < innerWidth / 4 ? prev : next)(); });
  let x0 = null;
  addEventListener('touchstart', e => { x0 = e.touches[0].clientX; }, { passive: true });
  addEventListener('touchend', e => {
    if (x0 === null) return; const dx = e.changedTouches[0].clientX - x0; x0 = null;
    if (Math.abs(dx) > 40) (dx < 0 ? next : prev)();
  });
  setTimeout(() => { const h = document.getElementById('hint'); if (h) h.style.opacity = 0; }, 5000);

  const start = Math.max(1, Math.min(slides.length, parseInt(location.hash.slice(1)) || 1)) - 1;
  show(start);
})();
"""


def main():
    deck = json.loads((SRC / 'deck.json').read_text(encoding='utf-8'))
    css = (SRC / 'deck.css').read_text(encoding='utf-8')
    fonts = sorted({f['href'] for f in deck.get('faces', {}).values()})
    parts = []
    for n, sid in enumerate(deck['order'], 1):
        s = (SRC / 'slides' / f'{sid}.html').read_text(encoding='utf-8')
        for blob, path in BLOBS.items():
            s = s.replace(f'/_blob/{blob}', path)
        s = re.sub(r'<section ', f'<section data-n="{n}" ', s, count=1)
        missing = re.findall(r'/_blob/([0-9a-f]{32})', s)
        if missing:
            raise SystemExit(f'Image inconnue dans {sid} : {missing}')
        parts.append(s)
    links = '\n'.join(f'<link rel="stylesheet" href="{h}">' for h in fonts)
    html = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{deck.get('title', 'Présentation')}</title>
<link rel="icon" href="assets/logo_navy.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
{links}
<style>
{css}
{PLAYER_CSS}
</style>
</head>
<body>
<div id="stage">
{''.join(parts)}
</div>
<div id="notes"></div>
<div id="prog"></div>
<div id="hint">→ / clic : avancer · ← : reculer · F : plein écran · N : notes</div>
<script>{PLAYER_JS}</script>
</body>
</html>
"""
    (ROOT / 'index.html').write_text(html, encoding='utf-8')
    print('index.html :', len(deck['order']), 'diapos')


if __name__ == '__main__':
    main()
