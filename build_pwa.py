import base64
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw


BASE = Path(__file__).resolve().parent
USERNAME = os.environ.get("GITHUB_USERNAME", "theitalis-cpu")
REPO = os.environ.get("GITHUB_REPO", "qna-explorer")
TOKEN = os.environ.get("GITHUB_TOKEN")


def make_icon(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = size // 7
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=(13, 27, 62))
    m = size * 0.12
    d.ellipse([m, m, size - m, size - m], fill=(20, 40, 90))

    def triangle_points(cx, cy, radius, angle_offset):
        return [
            (
                cx + radius * math.sin(math.radians(angle_offset + i * 120)),
                cy - radius * math.cos(math.radians(angle_offset + i * 120)),
            )
            for i in range(3)
        ]

    cx, cy = size / 2, size / 2
    tri_r = size * 0.30
    d.polygon(triangle_points(cx, cy, tri_r, 0), fill=(79, 142, 247, 230))
    d.polygon(triangle_points(cx, cy, tri_r, 180), fill=(124, 92, 247, 200))
    dot = size * 0.07
    d.ellipse([cx - dot, cy - dot, cx + dot, cy + dot], fill=(255, 255, 255, 200))
    return img


def write_assets():
    for size in (192, 512):
        make_icon(size).save(BASE / f"icon-{size}.png", "PNG")

    manifest = {
        "name": "שאלות ותשובות | דרך צדיקים",
        "short_name": 'שו"ת',
        "description": "ארכיון שאלות ותשובות — דרך צדיקים",
        "start_url": "/qna-explorer/",
        "scope": "/qna-explorer/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#0b0f1a",
        "theme_color": "#0d1b3e",
        "lang": "he",
        "dir": "rtl",
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    (BASE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    sw = """const CACHE = 'qna-v2';
const ASSETS = [
  '/qna-explorer/',
  '/qna-explorer/index.html',
  '/qna-explorer/qna_data.json',
  '/qna-explorer/manifest.json',
  '/qna-explorer/icon-192.png',
  '/qna-explorer/icon-512.png'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});
"""
    (BASE / "sw.js").write_text(sw, encoding="utf-8")


def github_request(method, path, payload=None):
    if not TOKEN:
        raise RuntimeError("Set GITHUB_TOKEN before deploying.")
    url = f"https://api.github.com/repos/{USERNAME}/{REPO}/contents/{path}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404 and method == "GET":
            return None
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {path} failed: {exc.code} {detail}") from exc


def push_file(remote_path, local_path, message):
    local_path = BASE / local_path
    raw = local_path.read_bytes()
    existing = github_request("GET", remote_path)
    payload = {
        "message": message,
        "content": base64.b64encode(raw).decode("ascii"),
    }
    if existing and existing.get("sha"):
        payload["sha"] = existing["sha"]
    result = github_request("PUT", remote_path, payload)
    print(f"[OK] {remote_path}: {result.get('commit', {}).get('sha', '')[:7]}")


def main():
    write_assets()
    subprocess.run([sys.executable, str(BASE / "gen_html.py")], check=True)
    files = [
        ("index.html", "QnA Explorer.html", "Update app"),
        ("qna_data.json", "qna_data.json", "Update Q&A data"),
        ("manifest.json", "manifest.json", "Update PWA manifest"),
        ("sw.js", "sw.js", "Update service worker"),
        ("icon-192.png", "icon-192.png", "Update app icon 192"),
        ("icon-512.png", "icon-512.png", "Update app icon 512"),
    ]
    for remote, local, message in files:
        push_file(remote, local, message)
    print(f"Live at: https://{USERNAME}.github.io/{REPO}/")


if __name__ == "__main__":
    main()
