"""Одноразово: скопировать assets/bg.png -> static/bg.png (запусти из корня empty-window)."""
import os
import shutil

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
src = os.path.join(root, 'assets', 'bg.png')
dst_dir = os.path.join(here, 'static')
dst = os.path.join(dst_dir, 'bg.png')
os.makedirs(dst_dir, exist_ok=True)
if not os.path.isfile(src):
    raise SystemExit(f'Нет источника: {src}')
shutil.copy2(src, dst)
print('OK', dst, os.path.getsize(dst))
