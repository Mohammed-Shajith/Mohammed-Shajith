#!/usr/bin/env python3
"""Builds the surf-zine profile images in assets/.

Each section is an SVG that wraps HTML/CSS in a <foreignObject>, with fonts
and the photo embedded, so it renders on GitHub exactly as designed.

Live numbers (streaks, commits, the tide chart) come from the GitHub GraphQL
API. Run by .github/workflows/profile.yml on a schedule.

  python scripts/build_profile.py            # fetch live data (needs GH_TOKEN)
  python scripts/build_profile.py --sample   # offline preview with sample data
"""
import base64
import datetime as dt
import json
import math
import os
import random
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
LOGIN = "Mohammed-Shajith"

# ---------------------------------------------------------------- content ---
# Edit these to change what the profile says. Rebuilds on the next run.

CURRENTLY_BUILDING = [
    ("exsy", "IN DEVELOPMENT", "yellow"),
    ("Data Intelligence Systems", "ACTIVE", "ink"),
    ("AI / ML Projects", "ACTIVE", "ink"),
]
MISSION = [
    "Build AI-powered applications",
    "Sharpen problem solving &amp; DSA",
    "Explore full-stack development",
    "Contribute to open source",
]
STACK = ["Python", "Java", "C", "C++", "SQL", "TensorFlow", "PyTorch", "scikit-learn",
         "NumPy", "FastAPI", "Streamlit", "React Native", "Flutter", "Next.js", "AWS",
         "Google Cloud", "MySQL", "Firebase"]
LEARNING = [("DSA", 0.60), ("Machine Learning", 0.72), ("Data Engineering", 0.55),
            ("System Design", 0.40), ("Cloud / DevOps", 0.48)]
EXSY_PROGRESS = 0.70

# ----------------------------------------------------------------- colors ---
PAPER = "#F9E547"
SUN = "#FFD21F"
INK = "#1530B8"
NAVY = "#0B1A6E"
CREAM = "#FBF6E8"
ORANGE = "#FF6B1A"
W = 880

# ------------------------------------------------------------------ fonts ---
FONT_FILES = {
    "anton": ("Anton", 400), "marker": ("Marker", 400), "grotesk-400": ("Grotesk", 400),
    "grotesk-500": ("Grotesk", 500), "grotesk-700": ("Grotesk", 700), "mono-700": ("Mono", 700),
}


def b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()


def font_css(names):
    out = []
    for n in names:
        fam, wt = FONT_FILES[n]
        out.append(f"@font-face{{font-family:'{fam}';font-weight:{wt};"
                   f"src:url(data:font/woff2;base64,{b64(ASSETS / 'fonts' / (n + '.woff2'))}) format('woff2');}}")
    return "".join(out)


BASE_CSS = f"""
*{{box-sizing:border-box}}
.root{{width:{W}px;font-family:'Grotesk',sans-serif;color:{NAVY};position:relative;overflow:hidden;border-radius:22px;
  background-color:{PAPER};background-image:radial-gradient(rgba(11,26,110,0.08) 1px,transparent 1.3px);background-size:7px 7px}}
.anton{{font-family:'Anton',sans-serif;text-transform:uppercase;font-weight:400}}
.marker{{font-family:'Marker',cursive}}
.mono{{font-family:'Mono',monospace;font-weight:700}}
.num{{font-family:'Anton',sans-serif;font-size:78px;line-height:0.8;color:{NAVY};padding:6px 8px 0;display:inline-block;position:relative;z-index:0}}
.blob::before{{content:'';position:absolute;left:-6px;right:-8px;top:2px;bottom:-8px;background:var(--bg);z-index:-1;
  animation:morph 7s ease-in-out infinite,jiggle 3.6s ease-in-out infinite;animation-delay:var(--d,0s)}}
@keyframes jiggle{{0%,100%{{transform:rotate(-8deg) scale(1)}}50%{{transform:rotate(8deg) scale(1.07)}}}}
@keyframes fillbar{{0%{{stroke-dasharray:0 999}}45%,100%{{stroke-dasharray:var(--to) 999}}}}
.fillbar{{animation:fillbar 5s cubic-bezier(.3,.7,.2,1) infinite;animation-delay:var(--d,0s)}}
@keyframes flow{{to{{stroke-dashoffset:-72}}}}
.flow{{animation:flow 1.8s linear infinite}}
@keyframes flicker{{0%,100%{{transform:scale(1,1) skewX(0)}}25%{{transform:scale(.96,1.07) skewX(-3deg)}}50%{{transform:scale(1.03,.95) skewX(2deg)}}75%{{transform:scale(.98,1.05) skewX(3deg)}}}}
.flicker{{animation:flicker 1.1s ease-in-out infinite;transform-origin:50% 100%}}
@keyframes cool{{0%,100%{{transform:rotate(11deg) translateY(0)}}50%{{transform:rotate(6deg) translateY(-3px)}}}}
@keyframes ring{{0%,100%{{r:5}}50%{{r:7}}}}
.pulse-ring{{animation:ring 1.6s ease-in-out infinite}}
.cool{{animation:cool 3s ease-in-out infinite}}
@keyframes glint{{0%,60%{{transform:translateX(-30px)}}100%{{transform:translateX(110px)}}}}
.glint{{animation:glint 3s ease-in-out infinite}}
.sec{{display:flex;align-items:flex-end;gap:14px}}
.sec .t{{font-family:'Anton',sans-serif;font-size:36px;color:{INK};text-transform:uppercase;line-height:1}}
.pill{{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;border:2px solid {NAVY};border-radius:999px;background:{CREAM};font-size:14px;font-weight:500}}
.chip{{font-family:'Mono',monospace;font-weight:700;font-size:11px;padding:4px 10px;border-radius:999px}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.spin{{animation:spin 18s linear infinite}}
.spin-rev{{animation:spin 11s linear infinite reverse}}
.spin-slow{{animation:spin 30s linear infinite}}
@keyframes floaty{{0%,100%{{transform:translate(0,0) rotate(0)}}33%{{transform:translate(8px,-10px) rotate(6deg)}}66%{{transform:translate(-6px,6px) rotate(-4deg)}}}}
.floaty{{animation:floaty 7s ease-in-out infinite}}
@keyframes morph{{0%,100%{{border-radius:58% 42% 55% 45%/45% 55% 45% 55%}}50%{{border-radius:40% 60% 38% 62%/60% 40% 60% 40%}}}}
.morph{{animation:morph 6s ease-in-out infinite;border-radius:58% 42% 55% 45%/45% 55% 45% 55%}}
.floaty.morph{{animation:floaty 7s ease-in-out infinite,morph 6s ease-in-out infinite}}
.morph.wiggle{{animation:morph 6s ease-in-out infinite,wiggle 2.2s ease-in-out infinite}}
@keyframes pulse{{0%{{box-shadow:0 0 0 0 rgba(29,185,84,.6)}}100%{{box-shadow:0 0 0 10px rgba(29,185,84,0)}}}}
.pulse{{animation:pulse 1.6s ease-out infinite}}
@keyframes rise{{0%{{transform:translateY(0);opacity:0}}15%{{opacity:.9}}100%{{transform:translateY(-170px);opacity:0}}}}
.rise{{animation:rise 5s ease-in infinite}}
@keyframes march{{to{{stroke-dashoffset:-60}}}}
.march{{animation:march 2.5s linear infinite}}
@keyframes wiggle{{0%,100%{{transform:rotate(-8deg)}}50%{{transform:rotate(8deg)}}}}
.wiggle{{animation:wiggle 2.2s ease-in-out infinite}}
@keyframes glide{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(60px,-14px)}}}}
.glide{{animation:glide 8s ease-in-out infinite}}
@keyframes sunpulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.06)}}}}
.sunpulse{{animation:sunpulse 5s ease-in-out infinite}}
@keyframes drift{{from{{transform:translateX(0)}}to{{transform:translateX(-440px)}}}}
.drift{{animation:drift 12s linear infinite}}
@keyframes bob{{0%,100%{{transform:translateY(0) rotate(-6deg)}}50%{{transform:translateY(-6px) rotate(-2deg)}}}}
.bob{{animation:bob 4s ease-in-out infinite}}
@keyframes grow{{from{{stroke-dashoffset:var(--len)}}to{{stroke-dashoffset:0}}}}
@keyframes blink{{50%{{opacity:.25}}}}
.blink{{animation:blink 1.4s steps(1) infinite}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""

SVGNS = 'xmlns="http://www.w3.org/2000/svg"'


def wrap(name, height, body, fonts, title):
    css = font_css(fonts) + BASE_CSS
    svg = (f'<svg {SVGNS} width="{W}" height="{height}" viewBox="0 0 {W} {height}" role="img" aria-label="{title}">'
           f'<title>{title}</title>'
           f'<foreignObject x="0" y="0" width="{W}" height="{height}">'
           f'<div xmlns="http://www.w3.org/1999/xhtml"><style>{css}</style>'
           f'<div class="root" style="height:{height}px">{body}</div></div>'
           f'</foreignObject></svg>')
    (ASSETS / f"{name}.svg").write_text(svg, encoding="utf-8")


def wave_squiggle(color, w=44, h=18):
    return (f'<svg {SVGNS} width="{w}" height="{h}" viewBox="0 0 44 18" fill="none" stroke="{color}" '
            f'stroke-width="3" stroke-linecap="round"><path d="M2 12 C 8 2, 16 2, 22 10 C 28 2, 36 2, 42 12"/></svg>')


def star(color, size):
    return (f'<svg {SVGNS} width="{size}" height="{size}" viewBox="0 0 54 54" fill="none" stroke="{color}" '
            f'stroke-width="4" stroke-linecap="round"><path d="M27 4v46M4 27h46M11 11l32 32M43 11L11 43"/></svg>')


def burst(color, size, points=12):
    pts = []
    for k in range(points * 2):
        r = 50 if k % 2 == 0 else 34
        a = math.pi * k / points
        pts.append(f"{50 + r * math.sin(a):.1f},{50 - r * math.cos(a):.1f}")
    return (f'<svg {SVGNS} width="{size}" height="{size}" viewBox="0 0 100 100">'
            f'<polygon points="{" ".join(pts)}" fill="{color}" opacity="0.28"/></svg>')


def flame(w):
    return (f'<svg {SVGNS} width="{w}" height="{w * 80 / 60:.0f}" viewBox="0 0 60 80">'
            '<path d="M30 2 C 36 18, 54 28, 54 50 C 54 66, 43 78, 30 78 C 17 78, 6 66, 6 50 C 6 38, 14 30, 18 22 C 20 32, 24 36, 28 38 C 26 26, 26 14, 30 2Z" fill="#F0441A"/>'
            '<path d="M30 22 C 34 34, 47 41, 47 56 C 47 68, 39 76, 30 76 C 21 76, 13 68, 13 56 C 13 48, 18 43, 21 39 C 23 47, 26 50, 29 50 C 27 41, 27 31, 30 22Z" fill="#FF8A1A"/>'
            '<path d="M30 44 C 33 53, 41 57, 41 65 C 41 72, 36 76, 30 76 C 24 76, 19 72, 19 65 C 19 60, 23 57, 26 54 C 27 58, 29 59, 30 58 C 29 53, 29 49, 30 44Z" fill="#FFD84A"/></svg>')


def shades_svg(w):
    return (f'<svg {SVGNS} width="{w}" height="{w / 3:.0f}" viewBox="0 0 96 32" fill="none">'
            '<defs><clipPath id="lens"><path d="M8 7 H40 C42 7 43 9 42 12 L39 23 C37 28 33 30 27 30 H19 C12 30 8 26 7 20 L5 11 C5 8 6 7 8 7Z M56 7 H88 C90 7 91 8 91 11 L89 20 C88 26 84 30 77 30 H69 C63 30 59 28 57 23 L54 12 C53 9 54 7 56 7Z"/></clipPath></defs>'
            '<path d="M1 9 H95" stroke="#0B1A6E" stroke-width="3.5" stroke-linecap="round"/>'
            '<path d="M8 7 H40 C42 7 43 9 42 12 L39 23 C37 28 33 30 27 30 H19 C12 30 8 26 7 20 L5 11 C5 8 6 7 8 7Z M56 7 H88 C90 7 91 8 91 11 L89 20 C88 26 84 30 77 30 H69 C63 30 59 28 57 23 L54 12 C53 9 54 7 56 7Z" fill="#0B1A6E"/>'
            '<g clip-path="url(#lens)"><g class="glint"><path d="M0 34 L14 0 H20 L6 34Z M10 34 L24 0 H27 L13 34Z" fill="#FFFFFF" opacity="0.55"/></g></g></svg>')


def wavy_arrow(color):
    return (f'<svg {SVGNS} width="38" height="16" viewBox="0 0 38 16" fill="none" stroke="{color}" stroke-width="2.5">'
            f'<path d="M1 8 c6 -8 10 8 16 0 s10 8 16 0"/><path d="M30 3l6 5-6 5"/></svg>')


# ============================================================ TOP SECTION ===
def build_top():
    photo = b64(ASSETS / "photo.jpg")
    icon = lambda d: (f'<svg {SVGNS} width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="{NAVY}" '
                      f'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">{d}</svg>')
    building = "".join(
        f'<div style="display:flex;align-items:center;gap:10px"><span style="font-weight:700;font-size:16px">{n}</span>'
        f'<span style="flex:1;border-bottom:2px dotted {NAVY}"></span>'
        f'<span class="chip" style="background:{SUN if c == "yellow" else INK};color:{NAVY if c == "yellow" else CREAM}">{s}</span></div>'
        for n, s, c in CURRENTLY_BUILDING)
    mission = "".join(
        f'<div style="display:flex;gap:10px;align-items:center">{wave_squiggle(INK, 22, 10)}<span>{m}</span></div>' for m in MISSION)

    def build_item(path, title, text):
        return (f'<div style="display:flex;flex-direction:column;gap:8px">'
                f'<svg {SVGNS} width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="{SUN}" stroke-width="1.6" '
                f'stroke-linecap="round" stroke-linejoin="round">{path}</svg>'
                f'<b class="mono" style="font-size:13px">{title}</b><span style="font-size:13px;opacity:.88">{text}</span></div>')

    body = f"""
<div style="position:relative;height:560px;padding:26px 36px 0">
  <div class="mono" style="display:flex;justify-content:space-between;align-items:center;font-size:13px;color:{INK};letter-spacing:1px">
    <span>SHJ // DATA SURF LAB &#8212;&#8212;&#8212; &#8594;</span>
    <span style="display:flex;gap:22px"><span>AI</span><span>DATA</span><span>SOFTWARE</span><span>BUILDER</span></span>
  </div>
  <div style="position:absolute;right:40px;top:84px;width:330px;height:330px;border-radius:50%;background:{SUN};box-shadow:inset 0 0 0 10px {PAPER}, inset 0 0 0 13px {INK}"></div>
  <div class="spin" style="position:absolute;right:20px;top:64px;width:370px;height:370px">
    <svg {SVGNS} width="370" height="370" viewBox="0 0 370 370" fill="none"><circle cx="185" cy="185" r="178" stroke="{INK}" stroke-width="2.5" stroke-dasharray="4 10"/><circle cx="185" cy="7" r="7" fill="{ORANGE}"/><circle cx="7" cy="185" r="4" fill="{INK}"/></svg>
  </div>
  <div class="spin-rev" style="position:absolute;right:52px;top:96px;width:306px;height:306px">
    <svg {SVGNS} width="306" height="306" viewBox="0 0 306 306" fill="none"><circle cx="153" cy="153" r="150" stroke="{NAVY}" stroke-width="1.5" stroke-dasharray="40 14 4 14"/><circle cx="300" cy="153" r="5" fill="{CREAM}" stroke="{NAVY}" stroke-width="2"/></svg>
  </div>
  <img src="data:image/jpeg;base64,{photo}" alt="" style="position:absolute;right:62px;top:106px;width:286px;height:286px;border-radius:50%;object-fit:cover"/>
  <div class="floaty morph" style="position:absolute;right:352px;top:330px;width:46px;height:40px;background:{ORANGE}"></div>
  <div class="spin-slow" style="position:absolute;right:300px;top:70px;width:54px;height:54px">{star(INK, 54)}</div>
  <div class="glide" style="position:absolute;right:390px;top:200px">{wave_squiggle(NAVY)}</div>
  <div class="anton" style="position:relative;margin-top:34px;font-size:104px;line-height:0.88;color:{INK};letter-spacing:-1px">Mohammed<br/>Shajith</div>
  <div class="bob" style="position:absolute;left:372px;top:88px">{star(ORANGE, 28)}</div>
  <div class="marker" style="font-size:30px;color:{INK};margin-top:18px;transform:rotate(-4deg);transform-origin:left;line-height:1.1">AI engineer<br/>&amp; developer &#8592;</div>
  <div class="marker" style="position:absolute;right:26px;top:430px;font-size:18px;line-height:1.15;color:{INK};transform:rotate(8deg)">"build<br/>learn<br/>debug<br/>repeat"</div>
  <div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:30px;max-width:470px;position:relative">
    <span class="pill">{icon('<path d="M12 22s7-7 7-12a7 7 0 1 0-14 0c0 5 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/>')}India</span>
    <span class="pill">{icon('<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c3 2 9 2 12 0v-5"/>')}SRMIST</span>
    <span class="pill">{icon('<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>')}Open to opportunities</span>
    <span class="pill"><span class="pulse" style="width:10px;height:10px;border-radius:50%;background:#1DB954"></span>Currently building</span>
  </div>
</div>
<svg {SVGNS} style="position:absolute;left:0;top:470px" width="880" height="120" viewBox="0 0 880 120" preserveAspectRatio="none" fill="none">
  <path d="M0 62 C 90 20, 170 90, 270 58 S 450 18, 560 60 S 760 100, 880 44 L880 120 L0 120Z" fill="{INK}"/>
  <path d="M0 84 C 100 52, 190 112, 300 82 S 480 44, 590 84 S 780 116, 880 70 L880 120 L0 120Z" fill="{CREAM}"/>
</svg>

<div style="background:{CREAM};padding:30px 36px 44px;display:grid;grid-template-columns:1.1fr 1fr;gap:36px;position:relative">
  <div style="display:flex;flex-direction:column;gap:14px">
    <div class="sec"><span class="num blob" style="--bg:{SUN};--d:-0.7s">01</span><span class="t">Who am I?</span></div>
    <p style="margin:0;font-size:15.5px;line-height:1.6">Artificial Intelligence student and developer focused on <b>Machine Learning</b>, <b>Data Engineering</b>, software development and intelligent applications.</p>
    <p style="margin:0;font-size:15.5px;line-height:1.6">I enjoy taking an idea from:</p>
    <div class="anton" style="display:flex;align-items:center;gap:8px;font-size:22px;letter-spacing:1px">
      <span style="padding:6px 14px;border-radius:999px;background:{SUN};color:{NAVY}">Idea</span>{wavy_arrow(INK)}
      <span style="padding:6px 14px;border-radius:999px;background:{INK};color:{CREAM}">System</span>{wavy_arrow(INK)}
      <span style="padding:4px 12px;border-radius:999px;border:2.5px solid {NAVY};color:{NAVY}">Product</span>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:6px">
      <span class="chip" style="border:1.5px solid {NAVY}">AI / ML</span><span class="chip" style="border:1.5px solid {NAVY}">DATA ENGINEERING</span>
      <span class="chip" style="border:1.5px solid {NAVY}">SOFTWARE DEV</span><span class="chip" style="border:1.5px solid {NAVY}">AUTOMATION</span>
    </div>
  </div>
  <div style="display:flex;flex-direction:column;gap:14px;position:relative">
    <div class="sec"><span class="num blob" style="--bg:{SUN};--d:-1.4s">02</span><span class="t">Currently building</span></div>
    <div style="border:2.5px solid {NAVY};border-radius:22px 34px 20px 30px;background:#fff;padding:16px 18px;display:flex;flex-direction:column;gap:12px;box-shadow:6px 6px 0 {NAVY}">
      <div class="mono" style="font-size:11px;color:{INK}">&gt; LIVE_FEED.status<span class="blink">_</span></div>
      {building}
    </div>
    <div style="display:flex;flex-direction:column;gap:7px;font-size:14.5px;margin-top:4px">{mission}</div>
    <div class="morph wiggle marker" style="position:absolute;right:-18px;bottom:-40px;width:126px;height:118px;background:{SUN};display:flex;align-items:center;justify-content:center;font-size:16px;line-height:1.05;text-align:center;color:{NAVY}">simple<br/>ideas,<br/>real<br/>impact</div>
  </div>
</div>

<svg {SVGNS} style="display:block;background:{CREAM}" width="880" height="50" viewBox="0 0 880 50" preserveAspectRatio="none"><path d="M0 50 L0 26 C 120 0, 230 46, 360 22 S 600 0, 720 26 S 840 40, 880 18 L880 50Z" fill="{INK}"/></svg>
<div style="background:{INK};padding:10px 36px 44px;color:{CREAM};position:relative;overflow:hidden;height:250px">
  <span class="rise" style="position:absolute;left:250px;bottom:0;width:10px;height:10px;border-radius:50%;border:2px solid {SUN}"></span>
  <span class="rise" style="position:absolute;left:470px;bottom:0;width:7px;height:7px;border-radius:50%;background:{CREAM};animation-delay:1.6s"></span>
  <span class="rise" style="position:absolute;left:640px;bottom:0;width:13px;height:13px;border-radius:50%;border:2px solid {CREAM};animation-delay:3s"></span>
  <span class="rise" style="position:absolute;left:800px;bottom:0;width:8px;height:8px;border-radius:50%;background:{SUN};animation-delay:2.2s"></span>
  <div class="sec"><span class="num blob" style="color:{SUN};--bg:#2C49D6;--d:-1.3s">03</span><span class="t" style="color:{SUN}">What I build</span><span class="marker" style="margin-left:auto;font-size:22px;color:{SUN}">~ ride the data wave</span></div>
  <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:20px;margin-top:26px">
    {build_item('<path d="M9 3a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 2 5 3 3 0 0 0 6 2V5a2 2 0 0 0-3-2z"/><path d="M15 3a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-2 5 3 3 0 0 1-6 2"/>', 'AI APPLICATIONS', 'ML models &#8594; APIs &#8594; web &amp; mobile apps')}
    {build_item('<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>', 'DATA SYSTEMS', 'Pipelines &#8594; validation &#8594; analytics')}
    {build_item('<path d="M8 6l-6 6 6 6"/><path d="M16 6l6 6-6 6"/><path d="M14 3l-4 18"/>', 'SOFTWARE PRODUCTS', 'Full-stack apps and developer tools')}
    {build_item('<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>', 'AUTOMATION TOOLS', 'Tools that save time and smooth workflows')}
  </div>
</div>
"""
    wrap("top", TOP_H, body, ["anton", "marker", "grotesk-400", "grotesk-500", "grotesk-700", "mono-700"],
         "Mohammed Shajith - AI engineer and developer")


# ======================================================= PROJECTS SECTION ===
def build_projects():
    def tags(items, style):
        return "".join(f'<span style="font-size:11.5px;padding:3px 10px;border-radius:999px;{style}">{t}</span>' for t in items)

    L = 96
    done = L * EXSY_PROGRESS
    body = f"""
<div style="padding:30px 36px 36px;display:flex;flex-direction:column;gap:22px;position:relative">
  <div class="sec"><span class="num blob" style="--bg:{CREAM};--d:-2.1s">04</span><span class="t">Featured projects</span>
    <span class="marker wiggle" style="font-size:26px;color:{INK};display:inline-block">&#8592;</span>
    <span class="floaty morph" style="width:22px;height:20px;background:{ORANGE};display:inline-block;margin-bottom:24px"></span>
    <span class="mono" style="margin-left:auto;font-size:12px;color:{INK}">ALL REPOS &#8594; BELOW</span></div>
  <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;height:290px">
    <div style="background:{INK};color:{CREAM};border-radius:26px 18px 30px 16px;padding:20px;display:flex;flex-direction:column;gap:12px;position:relative">
      <span class="chip" style="position:absolute;top:-12px;right:16px;background:{SUN};color:{NAVY};transform:rotate(4deg)">[01]</span>
      <svg {SVGNS} width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="{SUN}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8z"/><path class="march" stroke-dasharray="6 4" d="M3 12h5l2-3 3 6 2-3h6"/></svg>
      <div class="anton" style="font-size:26px;letter-spacing:.5px;text-transform:none">HeartSense AI</div>
      <div style="font-size:13.5px;line-height:1.5;opacity:.92">Cardiac risk prediction app using ML with a mobile interface.</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:auto">{tags(["Python", "scikit-learn", "React Native"], "background:#2C49D6")}</div>
      <div class="mono" style="font-size:11px;color:{SUN}">REPO DROPPING SOON</div>
    </div>
    <div style="background:{SUN};border:2.5px solid {NAVY};border-radius:16px 30px 18px 28px;padding:20px;display:flex;flex-direction:column;gap:12px;position:relative">
      <span class="chip" style="position:absolute;top:-12px;right:16px;background:{INK};color:{CREAM};transform:rotate(-4deg)">[02]</span>
      <svg {SVGNS} width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="{NAVY}" stroke-width="1.8" stroke-linecap="round"><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>
      <div class="anton" style="font-size:24px;letter-spacing:.5px;line-height:1.05;text-transform:none">Data Quality Intelligence Pipeline</div>
      <div style="font-size:13.5px;line-height:1.5">LLM-based data quality audit system with multi-pass analysis and reports.</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:auto">{tags(["Python", "LLM", "Streamlit"], f"border:1.5px solid {NAVY}")}</div>
    </div>
    <div style="background:{CREAM};border:2.5px solid {NAVY};border-radius:30px 16px 26px 20px;padding:20px;display:flex;flex-direction:column;gap:12px;position:relative">
      <span class="chip" style="position:absolute;top:-12px;right:16px;background:{SUN};color:{NAVY};transform:rotate(3deg)">[03]</span>
      <svg {SVGNS} width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round"><path d="M12 2l10 5-10 5L2 7z"/><path d="M2 12l10 5 10-5"/><path d="M2 17l10 5 10-5"/></svg>
      <div class="anton" style="font-size:26px;letter-spacing:.5px;text-transform:none">exsy</div>
      <div style="font-size:13.5px;line-height:1.5">A personal productivity and automation platform.</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px">{tags(["React Native", "FastAPI", "AI tools"], f"border:1.5px solid {NAVY}")}</div>
      <div style="display:flex;align-items:center;gap:8px;margin-top:auto"><span class="chip" style="background:{INK};color:{CREAM}">BUILDING<span class="blink">...</span></span>
        <svg {SVGNS} width="100" height="12" viewBox="0 0 100 12" fill="none"><path d="M2 6 C 12 0, 22 12, 32 6 S 52 0, 62 6 S 82 12, 98 6" stroke="#E3DCC5" stroke-width="4" stroke-linecap="round"/><path class="fillbar" style="--to:{done:.0f}px" d="M2 6 C 12 0, 22 12, 32 6 S 52 0, 62 6 S 82 12, 98 6" stroke="{INK}" stroke-width="4" stroke-linecap="round" stroke-dasharray="{done:.0f} 999"/><path class="flow" d="M2 6 C 12 0, 22 12, 32 6 S 52 0, 62 6 S 82 12, 98 6" stroke="#FFFFFF" stroke-opacity="0.5" stroke-width="1.5" stroke-linecap="round" stroke-dasharray="3 21"/></svg>
        <span class="mono" style="font-size:11px">{EXSY_PROGRESS * 100:.0f}%</span></div>
    </div>
  </div>
</div>
"""
    wrap("projects", PROJECTS_H, body, ["anton", "marker", "grotesk-400", "grotesk-500", "mono-700"], "Featured projects")


# ========================================================== STATS SECTION ===
def build_stats(data):
    stack = "".join(
        f'<span style="font-size:13.5px;font-weight:500;padding:6px 14px;border:2px solid {NAVY};border-radius:999px;'
        f'background:{INK if i % 5 == 0 else SUN if i % 7 == 3 else CREAM};color:{CREAM if i % 5 == 0 else NAVY}">{n}</span>'
        for i, n in enumerate(STACK))
    days = data["days"]  # one list per week (oldest first) of [date, count]
    weeks = [[c for _, c in w] for w in days]
    # partial first/last weeks are scaled to a 7-day rate so the line doesn't dip at the edges
    contrib_week = [sum(w) * 7 / len(w) for w in weeks]
    commit_week = [v * 7 / len(w) for v, w in zip(data["commit_weeks"], weeks)]
    cw = 758                      # inner width of the tide card
    ncols = len(weeks)
    LW = 0
    pitch = (cw - LW) / ncols     # one dot column
    dot = pitch - 3
    TIP, CH, MR = 50, 112, 18     # tooltip strip, chart height, month-label row
    gy = TIP + CH + MR            # top of the dot grid
    plot_h = gy + 7 * pitch
    xs = [LW + i * pitch + dot / 2 for i in range(ncols)]  # line points sit above their dot column
    peak = max(max(contrib_week), max(commit_week), 1)
    scaled_c = [v / peak for v in contrib_week]
    scaled_m = [v / peak for v in commit_week]

    # both lines share one scale
    def scaled_path(vals):
        pts = [(xs[i], CH - 8 - v * 88) for i, v in enumerate(vals)]
        d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            mx = (x0 + x1) / 2
            d += f" C{mx:.1f} {y0:.1f} {mx:.1f} {y1:.1f} {x1:.1f} {y1:.1f}"
        return d
    line = scaled_path(scaled_c)
    line2 = scaled_path(scaled_m)
    area = line + f" L{xs[-1]:.1f} {CH} L{xs[0]:.1f} {CH} Z"
    pk = max(range(ncols), key=lambda i: contrib_week[i])
    pk_x, pk_y = xs[pk], CH - 8 - scaled_c[pk] * 88
    pk_anchor = "end" if pk_x > cw - 140 else "start"
    pk_dx = -10 if pk_anchor == "end" else 10
    pk_label = f"peak week &#183; {round(contrib_week[pk])}"
    flat = [(d, c) for w in days for d, c in w]
    best_day = max(flat, key=lambda t: t[1])
    fmt = lambda iso: dt.date.fromisoformat(iso).strftime("%d %b %Y")

    # shade by quartiles of the distinct daily counts, so quiet 1-commit days and busy days look different
    levels = sorted({c for w in weeks for c in w if c > 0}) or [1]
    q = lambda p: levels[min(len(levels) - 1, int(p * len(levels)))]
    cuts = [q(0.25), q(0.5), q(0.75)] if len(levels) >= 4 else levels[:-1] + [10 ** 9] * (4 - len(levels))
    shades = ["#E7E0C8", "#B9C3F0", "#7D8FE6", "#3D57D4", INK]

    def shade(c):
        if c == 0:
            return shades[0]
        return shades[1 + sum(c > t for t in cuts)]

    pos = {}  # date -> (x, y) top-left of its dot, on its real weekday row (Sun..Sat)
    for c, w in enumerate(days):
        for d, v in w:
            r = (dt.date.fromisoformat(d).weekday() + 1) % 7
            pos[d] = (LW + c * pitch, gy + r * pitch)
    top3 = []  # three busiest days, spread out so their labels don't collide
    for d, v in sorted(flat, key=lambda t: -t[1]):
        if v > 0 and all(abs((dt.date.fromisoformat(d) - dt.date.fromisoformat(o)).days) > 21 for o, _ in top3):
            top3.append((d, v))
        if len(top3) == 3:
            break
    top3_dates = {d for d, _ in top3}
    dots = "".join(
        f'<span style="position:absolute;left:{pos[d][0]:.1f}px;top:{pos[d][1]:.1f}px;width:{dot:.1f}px;height:{dot:.1f}px;'
        f'border-radius:50%;background:{shade(v)}'
        + (f';box-shadow:0 0 0 2px {CREAM},0 0 0 3.5px {ORANGE}' if (d, v) == best_day else '') + '"></span>'
        for d, v in flat)
    wk = "".join(f'<span class="mono" style="position:absolute;left:0;top:{gy + r * pitch - 1:.1f}px;font-size:9.5px;line-height:{dot:.0f}px">{n}</span>'
                 for r, n in ((1, "MON"), (3, "WED"), (5, "FRI")))

    # A: handwritten callouts on the three busiest days
    callouts = ""
    for rank, (d, v) in enumerate(top3):
        x, y = pos[d]
        left_side = x > cw - 90
        bx = x - 46 if left_side else x + dot + 8
        by = y - 20
        lx1, lx2 = (x - 2, bx + 38) if left_side else (x + dot + 1, bx + 2)
        callouts += (f'<svg {SVGNS} style="position:absolute;left:0;top:0" width="{cw}" height="{plot_h:.0f}" fill="none">'
                     f'<path d="M{lx1:.1f} {y + dot / 2:.1f} Q {(lx1 + lx2) / 2:.1f} {by + 4:.1f} {lx2:.1f} {by + 9:.1f}" stroke="{ORANGE}" stroke-width="1.6"/></svg>'
                     f'<span class="marker" style="position:absolute;left:{bx:.1f}px;top:{by:.1f}px;font-size:13px;line-height:1;padding:3px 7px;'
                     f'background:{SUN};border:1.5px solid {NAVY};border-radius:10px;transform:rotate({(-4, 3, -2)[rank]}deg);white-space:nowrap">{v}</span>')

    # B: a self-running "hover" that tours the year, one month at a time
    month_cols = {}
    for c, w in enumerate(days):
        month_cols.setdefault(w[0][0][:7], []).append(c)
    month_days = {}
    for d, v in flat:
        month_days.setdefault(d[:7], []).append((d, v))
    tour_months = [m for m in sorted(month_cols) if m in month_days]
    n_m = len(tour_months)
    slot = 2.4
    total = n_m * slot
    vis = 100 / n_m
    tour = ""
    labels = ""
    for i, m in enumerate(tour_months):
        cols = month_cols[m]
        x0 = LW + cols[0] * pitch - 3
        wband = len(cols) * pitch + 3
        md = month_days[m]
        tot = sum(v for _, v in md)
        active = sum(1 for _, v in md if v > 0)
        bd, bv = max(md, key=lambda t: t[1])
        name = dt.date.fromisoformat(m + "-01").strftime("%b %Y").upper()
        tw = 330
        tx = min(max(x0 + wband / 2 - tw / 2, 0), cw - tw)
        ax = x0 + wband / 2 - tx
        tour += (f'<div class="tour" style="animation-delay:{i * slot:.1f}s">'
                 f'<div style="position:absolute;left:{x0:.1f}px;top:{TIP - 4}px;width:{wband:.1f}px;height:{plot_h - TIP + 7:.1f}px;'
                 f'border:2px dashed {INK};border-radius:10px;background:rgba(255,210,31,0.22)"></div>'
                 f'<div class="mono" style="position:absolute;left:{tx:.1f}px;top:0;width:{tw}px;padding:7px 10px;border-radius:10px;'
                 f'background:{NAVY};color:{CREAM};font-size:10.5px;line-height:1.45;text-align:center">'
                 f'<span style="color:{SUN}">{name}</span> &#183; {tot} contributions &#183; {active} active days<br/>'
                 f'busiest: {dt.date.fromisoformat(bd).day} {dt.date.fromisoformat(bd).strftime("%b")} ({bv})'
                 f'<span style="position:absolute;left:{ax - 6:.1f}px;bottom:-6px;width:12px;height:12px;background:{NAVY};transform:rotate(45deg)"></span></div></div>')
        if len(cols) >= 2:
            labels += f'<span class="mono" style="position:absolute;left:{LW + cols[0] * pitch:.1f}px;top:{TIP + CH + 3}px;font-size:10px;color:{INK}">{name[:3]}</span>'
    # "flex days": days well above your usual pace get a flexing arm that cycles arm -> date -> count
    nz = sorted(v for _, v in flat if v > 0)
    usual = nz[len(nz) // 2] if nz else 1
    bar = max(usual * 2, nz[int(len(nz) * 0.9)] if nz else 2, 2)
    flex_days = []
    for d, v in sorted(flat, key=lambda t: -t[1]):
        if v < bar or len(flex_days) == 6:
            break
        if all(abs((dt.date.fromisoformat(d) - dt.date.fromisoformat(o)).days) > 24 for o, _ in flex_days):
            flex_days.append((d, v))
    arm = (f'<svg {SVGNS} width="30" height="30" viewBox="0 0 40 40" fill="none" stroke-linecap="round" style="overflow:visible">'
           f'<g class="shake">'
           f'<g class="pow" stroke="{ORANGE}" stroke-width="2.4"><path d="M10 13 L7 8"/><path d="M15 11 L15 5"/><path d="M20 13 L23 8"/></g>'
           f'<path d="M3 31 H23" stroke="{SUN}" stroke-width="9"/>'
           f'<ellipse class="bicep" cx="14" cy="25" rx="8.5" ry="6.5" fill="{SUN}"/>'
           f'<g class="forearm"><path d="M23 31 L27 13" stroke="{SUN}" stroke-width="8"/>'
           f'<rect x="21" y="3" width="12" height="11" rx="4.5" fill="{SUN}"/>'
           f'<path d="M24 8 H30" stroke="{NAVY}" stroke-width="1.4"/></g></g></svg>')
    flexers = ""
    for k, (d, v) in enumerate(flex_days):
        x, y = pos[d]
        bw, bh = 58, 36
        bx = min(max(x + dot / 2 - bw / 2, 0), cw - bw)
        by = y - bh - 7
        day = dt.date.fromisoformat(d)
        delay = -k * 1.7
        layer = lambda cls, inner: (f'<span class="{cls}" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;'
                                    f'animation-delay:{delay:.1f}s">{inner}</span>')
        flexers += (f'<span style="position:absolute;left:{x - 2:.1f}px;top:{y - 2:.1f}px;width:{dot + 4:.1f}px;height:{dot + 4:.1f}px;border-radius:50%;'
                    f'border:2px solid {ORANGE}"></span>'
                    f'<div class="flexpop" style="position:absolute;left:{bx:.1f}px;top:{by:.1f}px;width:{bw}px;height:{bh}px;animation-delay:{delay:.1f}s">'
                    f'<div style="position:absolute;inset:0;border-radius:14px;background:{NAVY};box-shadow:2px 2px 0 {ORANGE}"></div>'
                    f'<span style="position:absolute;left:{x + dot / 2 - bx - 5:.1f}px;bottom:-5px;width:10px;height:10px;background:{NAVY};transform:rotate(45deg)"></span>'
                    + layer("fx-a", arm)
                    + layer("fx-b mono", f'<span style="color:{CREAM};font-size:12px">{day.day} {day.strftime("%b")}</span>')
                    + layer("fx-c anton", f'<span style="color:{SUN};font-size:24px;line-height:1">{v}</span>')
                    + '</div>')
    flex_css = (".fx-b,.fx-c{opacity:0}"
                "@keyframes fxa{0%,30%{opacity:1}35%,95%{opacity:0}100%{opacity:1}}"
                "@keyframes fxb{0%,33%{opacity:0}38%,62%{opacity:1}67%,100%{opacity:0}}"
                "@keyframes fxc{0%,65%{opacity:0}70%,92%{opacity:1}97%,100%{opacity:0}}"
                ".fx-a{animation:fxa 6s infinite}.fx-b{animation:fxb 6s infinite}.fx-c{animation:fxc 6s infinite}"
                "@keyframes curl{0%,100%{transform:rotate(30deg)}45%,60%{transform:rotate(-10deg)}}"
                ".forearm{transform-origin:23px 31px;animation:curl 1s ease-in-out infinite}"
                "@keyframes bulge{0%,100%{transform:scale(.7,.7)}45%,60%{transform:scale(1.3,1.35)}}"
                ".bicep{transform-origin:14px 31px;animation:bulge 1s ease-in-out infinite}"
                "@keyframes pow{0%,35%,75%,100%{opacity:0;transform:scale(.6)}50%,60%{opacity:1;transform:scale(1)}}"
                ".pow{transform-origin:15px 14px;animation:pow 1s ease-in-out infinite}"
                "@keyframes shake{0%,40%,70%,100%{transform:translate(0,0)}47%{transform:translate(-1px,0)}53%{transform:translate(1px,0)}58%{transform:translate(-1px,0)}}"
                ".shake{animation:shake 1s linear infinite}"
                "@keyframes pop{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}"
                ".flexpop{animation:pop 1.6s ease-in-out infinite}")

    tour_css = (f"@keyframes tour{{0%{{opacity:0}}0.6%{{opacity:1}}{vis - 0.6:.2f}%{{opacity:1}}{vis:.2f}%,100%{{opacity:0}}}}"
                f".tour{{opacity:0;animation:tour {total:.1f}s linear infinite}}")
    updated = data["updated"]
    body = f"""
<div style="padding:30px 36px 20px;display:grid;grid-template-columns:1fr 1fr;gap:34px;position:relative">
  <div style="display:flex;flex-direction:column;gap:16px">
    <div class="sec"><span class="num blob" style="--bg:{CREAM};--d:-2.8s">05</span><span class="t">Tech stack</span></div>
    <div style="display:flex;flex-wrap:wrap;gap:8px">{stack}</div>
    <div class="marker" style="font-size:17px;color:{INK};transform:rotate(-2deg)">&#8627; the boards in my quiver</div>
  </div>
  <div style="display:flex;flex-direction:column;gap:16px">
    <div class="sec"><span class="num blob" style="--bg:{CREAM};--d:-3.5s">06</span><span class="t">Activity report</span>
      <span class="spin-slow" style="display:inline-block;width:30px;height:30px;margin-bottom:30px">{star(ORANGE, 30)}</span></div>
    <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px">
      <div style="background:{INK};color:{CREAM};border-radius:50% 50% 18px 18px;padding:18px 6px 14px;text-align:center"><div class="anton" style="font-size:38px;color:{SUN}">{data['commits']}</div><div class="mono" style="font-size:10.5px">COMMITS<br/>LAST YEAR</div></div>
      <div style="background:{SUN};border:2.5px solid {NAVY};border-radius:50% 50% 18px 18px;padding:16px 6px 12px;text-align:center;position:relative;overflow:hidden">
        <div class="spin-slow" style="position:absolute;left:50%;top:-8px;margin-left:-46px;width:92px;height:92px">{burst(ORANGE, 92)}</div>
        <div class="flicker" style="position:absolute;left:50%;top:-4px;margin-left:-22px;width:44px;height:59px">{flame(44)}</div>
        <div class="anton" style="font-size:38px;position:relative;z-index:1;text-shadow:0 0 6px {SUN},0 0 2px {SUN}">{data['current_streak']}<span style="font-size:18px"> d</span></div><div class="mono" style="font-size:10.5px">CURRENT<br/>STREAK</div></div>
      <div style="background:{CREAM};border:2.5px solid {NAVY};border-radius:50% 50% 18px 18px;padding:16px 6px 12px;text-align:center;position:relative">
        <div class="anton" style="font-size:38px;color:{INK};position:relative">{data['best_streak']}<span style="font-size:18px"> d</span>
          <div class="cool" style="position:absolute;left:50%;top:-28px;margin-left:-26px;width:72px;height:24px;z-index:2">{shades_svg(72)}</div></div><div class="mono" style="font-size:10.5px">BEST<br/>STREAK</div></div>
    </div>
    <div class="mono" style="display:flex;justify-content:space-between;font-size:11.5px;border-top:2px solid {NAVY};padding-top:10px">
      <span>CONTRIBS &#183; {data['contributions']}</span><span>PRs &#183; {data['prs']}</span><span>TOP LANG &#183; {data['top_lang']}</span></div>
    <div class="marker" style="font-size:14px;color:{INK}">auto-refreshed &#183; {updated}</div>
  </div>
</div>
<div style="margin:6px 36px 0;border:2.5px solid {NAVY};border-radius:28px 20px 34px 22px;background:{CREAM};padding:20px 22px;display:flex;flex-direction:column;gap:12px;position:relative">
  <div style="display:flex;justify-content:space-between;align-items:center"><span class="anton" style="font-size:24px;color:{INK}">Tide chart &#183; commits &amp; contributions</span><span class="mono" style="font-size:11px">{ncols} WEEKS &#8594; TODAY</span></div>
  <style>{tour_css}{flex_css}</style>
  <div style="position:relative;width:{cw}px;height:{plot_h:.0f}px">
    <svg {SVGNS} style="position:absolute;left:0;top:{TIP}px" width="{cw}" height="{CH}" viewBox="0 0 {cw} {CH}" fill="none">
      <path d="{area}" fill="{INK}" opacity="0.16"/>
      <path d="{line}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>
      <path class="march" d="{line2}" stroke="{ORANGE}" stroke-width="2.2" stroke-dasharray="5 5"/>
      <line x1="{pk_x:.1f}" y1="{pk_y:.1f}" x2="{pk_x:.1f}" y2="{CH}" stroke="{NAVY}" stroke-width="1" stroke-dasharray="2 3"/>
      <circle class="pulse-ring" cx="{pk_x:.1f}" cy="{pk_y:.1f}" r="5" fill="{SUN}" stroke="{NAVY}" stroke-width="2"/>
      <text x="{pk_x + pk_dx:.1f}" y="{max(pk_y - 2, 12):.1f}" text-anchor="{pk_anchor}" font-family="Mono" font-weight="700" font-size="10.5" fill="{NAVY}">{pk_label}</text>
    </svg>
    {labels}{dots}{tour}{flexers}
  </div>
  <div class="mono" style="font-size:11px;display:flex;align-items:center;gap:8px"><span style="width:11px;height:11px;border-radius:50%;background:{INK};box-shadow:0 0 0 2px {CREAM},0 0 0 3.5px {ORANGE}"></span>busiest day &#183; {fmt(best_day[0])} &#183; {best_day[1]} contributions &#183; the flexing arms mark your above-usual days</div>
  <div class="mono" style="display:flex;gap:18px;font-size:11px;align-items:center">
    <span style="display:flex;align-items:center;gap:6px"><span style="width:18px;height:3px;background:{INK}"></span>contributions / week</span>
    <span style="display:flex;align-items:center;gap:6px"><span style="width:18px;border-top:2px dashed {ORANGE}"></span>commits / week</span>
    <span style="margin-left:auto;display:flex;align-items:center;gap:4px">less {''.join(f'<span style="width:11px;height:11px;border-radius:50%;background:{s}"></span>' for s in shades)} more</span>
  </div>
</div>
"""
    wrap("stats", STATS_H, body, ["anton", "marker", "grotesk-500", "mono-700"], "Tech stack and live GitHub stats")


# ===================================================== LEARNING + CONNECT ===
def build_learning():
    L = 260
    rows = "".join(
        f'<div style="display:grid;grid-template-columns:140px 1fr;align-items:center;gap:12px;font-size:14px;font-weight:500"><span>{n}</span>'
        f'<svg {SVGNS} width="220" height="14" viewBox="0 0 220 14" fill="none">'
        f'<path d="M3 7 C 20 1, 37 13, 55 7 S 92 1, 110 7 S 147 13, 165 7 S 200 1, 217 7" stroke="{CREAM}" stroke-width="6" stroke-linecap="round"/>'
        f'<path class="fillbar" style="--to:{L * f:.0f}px;--d:{i * 0.35:.2f}s" d="M3 7 C 20 1, 37 13, 55 7 S 92 1, 110 7 S 147 13, 165 7 S 200 1, 217 7" stroke="{INK}" stroke-width="6" stroke-linecap="round" stroke-dasharray="{L * f:.0f} 999"/>'
        f'<path class="flow" d="M3 7 C 20 1, 37 13, 55 7 S 92 1, 110 7 S 147 13, 165 7 S 200 1, 217 7" stroke="#FFFFFF" stroke-opacity="0.45" stroke-width="2" stroke-linecap="round" stroke-dasharray="4 32"/></svg></div>'
        for i, (n, f) in enumerate(LEARNING))
    body = f"""
<div style="padding:30px 36px 0;display:grid;grid-template-columns:1fr 1fr;gap:34px;position:relative;height:100%;background:{SUN}">
  <div style="display:flex;flex-direction:column;gap:14px">
    <div class="sec"><span class="num blob" style="--bg:{CREAM};--d:-2.1s">07</span><span class="t" style="font-size:32px">Currently learning</span></div>
    {rows}
    <div class="marker" style="font-size:17px;transform:rotate(-3deg);margin-top:4px">"a little progress each day."</div>
  </div>
  <div style="display:flex;flex-direction:column;gap:16px;position:relative">
    <div class="sec"><span class="num blob" style="--bg:{CREAM};--d:-0.4s">08</span><span class="t" style="font-size:32px">Let's connect</span></div>
    <div class="marker" style="font-size:36px;line-height:1.05;color:{NAVY};transform:rotate(-5deg);margin-top:8px">Let's build<br/>something cool.</div>
    <div class="mono" style="font-size:12px;color:{INK};display:flex;align-items:center;gap:8px">LINKS JUST BELOW <span class="bob" style="display:inline-block">&#8595;</span></div>
    <div class="glide" style="position:absolute;right:30px;top:150px">{wave_squiggle(NAVY)}</div>
  </div>
</div>
"""
    wrap("learning", LEARNING_H, body, ["anton", "marker", "grotesk-500", "mono-700"], "Currently learning and contact")


def build_footer():
    body = f"""
<div style="background:{SUN};position:relative;height:190px;overflow:hidden">
  <div class="sunpulse" style="position:absolute;right:90px;top:30px;width:150px;height:150px;border-radius:50%;background:{ORANGE}"></div>
  <div class="spin-slow" style="position:absolute;right:65px;top:5px;width:200px;height:200px"><svg {SVGNS} width="200" height="200" viewBox="0 0 200 200" fill="none" stroke="{ORANGE}" stroke-width="3" stroke-linecap="round"><path d="M100 4v14M100 182v14M4 100h14M182 100h14M32 32l10 10M158 158l10 10M32 168l10-10M158 42l10-10"/></svg></div>
  <div class="glide" style="position:absolute;left:330px;top:40px">{wave_squiggle(NAVY, 40, 16)}</div>
  <div class="glide" style="position:absolute;left:420px;top:70px;animation-delay:2s">{wave_squiggle(NAVY, 26, 11)}</div>
  <div class="drift" style="position:absolute;left:0;bottom:0;width:1320px;height:120px">
    <svg {SVGNS} width="1320" height="120" viewBox="0 0 1320 120" fill="none">
      <path d="M0 50 C 55 20, 110 80, 220 50 S 385 20, 440 50 S 550 80, 660 50 S 825 20, 880 50 S 990 80, 1100 50 S 1265 20, 1320 50 L1320 120 L0 120Z" fill="{INK}"/>
      <path d="M0 78 C 55 58, 110 98, 220 78 S 385 58, 440 78 S 550 98, 660 78 S 825 58, 880 78 S 990 98, 1100 78 S 1265 58, 1320 78 L1320 120 L0 120Z" fill="{NAVY}"/>
    </svg>
  </div>
  <div class="mono" style="position:absolute;left:36px;top:30px;font-size:11px;color:{NAVY}">SHJ // ISSUE {dt.date.today().year} &#183; IDEA &#8594; SYSTEM &#8594; PRODUCT</div>
</div>
"""
    wrap("footer", 190, body, ["mono-700"], "Sunset footer")


def build_button(name, label, bg, fg, border):
    width = 26 + len(label) * 10
    body = (f'<div style="height:44px;display:flex;align-items:center;justify-content:center;background:transparent">'
            f'<span style="font-size:15px;font-weight:700;padding:10px 22px;border-radius:999px;background:{bg};color:{fg};'
            f'border:2px solid {border};white-space:nowrap">{label}</span></div>')
    svg = (f'<svg {SVGNS} width="{width + 24}" height="44" viewBox="0 0 {width + 24} 44" role="img" aria-label="{label}"><title>{label}</title>'
           f'<foreignObject x="0" y="0" width="{width + 24}" height="44"><div xmlns="http://www.w3.org/1999/xhtml">'
           f'<style>{font_css(["grotesk-700"])}*{{box-sizing:border-box}}div{{font-family:\'Grotesk\',sans-serif}}</style>{body}</div></foreignObject></svg>')
    (ASSETS / f"btn-{name}.svg").write_text(svg, encoding="utf-8")


TOP_H = 1292
PROJECTS_H = 448
STATS_H = 810
LEARNING_H = 330

# ================================================================== data ===
QUERY_YEAR = """query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){
contributionsCollection(from:$from,to:$to){contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""

QUERY_COMMITS = """query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){
contributionsCollection(from:$from,to:$to){commitContributionsByRepository(maxRepositories:100){
contributions(first:100){nodes{occurredAt commitCount}}}}}}"""

QUERY_MAIN = """query($login:String!){user(login:$login){createdAt
contributionsCollection{totalCommitContributions restrictedContributionsCount totalPullRequestContributions
contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}
}
repositories(ownerAffiliations:OWNER,isFork:false,first:100){nodes{languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}}}"""


def gql(token, query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-builder"})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if "errors" in out:
        raise RuntimeError(out["errors"])
    return out["data"]["user"]


def streaks(days):
    """days: sorted list of (date, count). Returns (current, best)."""
    best = run = 0
    for _, c in days:
        run = run + 1 if c > 0 else 0
        best = max(best, run)
    current = 0
    seq = list(days)
    if seq and seq[-1][1] == 0:  # today not yet counted: streak can still be alive from yesterday
        seq = seq[:-1]
    for _, c in reversed(seq):
        if c == 0:
            break
        current += 1
    return current, best


def fetch_live(token):
    u = gql(token, QUERY_MAIN, {"login": LOGIN})
    cc = u["contributionsCollection"]
    days = [[[d["date"], d["contributionCount"]] for d in w["contributionDays"]] for w in cc["contributionCalendar"]["weeks"]]
    weeks = days
    week_starts = [w["contributionDays"][0]["date"] for w in cc["contributionCalendar"]["weeks"]]

    # commits per week, fetched month by month so no repo hits the 100-day page limit
    commit_weeks = [0] * len(weeks)
    start = dt.datetime.fromisoformat(week_starts[0]).replace(tzinfo=dt.timezone.utc)
    end = dt.datetime.now(dt.timezone.utc)
    while start < end:
        stop = min(start + dt.timedelta(days=28), end)
        m = gql(token, QUERY_COMMITS, {"login": LOGIN, "from": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                       "to": stop.strftime("%Y-%m-%dT%H:%M:%SZ")})
        for repo in m["contributionsCollection"]["commitContributionsByRepository"]:
            for n in repo["contributions"]["nodes"]:
                day = n["occurredAt"][:10]
                for i in range(len(week_starts) - 1, -1, -1):
                    if day >= week_starts[i]:
                        commit_weeks[i] += n["commitCount"]
                        break
        start = stop

    # streaks across every year since the account was created
    all_days = {}
    start_year = int(u["createdAt"][:4])
    now = dt.datetime.now(dt.timezone.utc)
    for year in range(start_year, now.year + 1):
        frm = f"{year}-01-01T00:00:00Z"
        to = now.strftime("%Y-%m-%dT%H:%M:%SZ") if year == now.year else f"{year}-12-31T23:59:59Z"
        y = gql(token, QUERY_YEAR, {"login": LOGIN, "from": frm, "to": to})
        for w in y["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                all_days[d["date"]] = d["contributionCount"]
    today = now.date().isoformat()
    history = sorted((k, v) for k, v in all_days.items() if k <= today)
    current, best = streaks(history)

    langs = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    top_lang = max(langs, key=langs.get) if langs else "Python"

    return {
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "contributions": cc["contributionCalendar"]["totalContributions"],
        "prs": cc["totalPullRequestContributions"],
        "current_streak": current, "best_streak": best, "top_lang": top_lang,
        "days": days, "commit_weeks": commit_weeks,
        "updated": now.strftime("%d %b %Y, %H:%M UTC"),
    }


def sample_data():
    rnd = random.Random(7)
    weeks = []
    for i in range(53):
        wave = 0.5 + 0.5 * math.sin(i / 4.2)
        weeks.append([max(0, int(rnd.random() * 6 * wave + rnd.random() * 2 - 0.6)) for _ in range(7)])
    weeks[-1] = weeks[-1][:4]
    start = dt.date(2025, 10, 5)  # a Sunday
    days = [[[(start + dt.timedelta(days=7 * i + j)).isoformat(), c] for j, c in enumerate(w)] for i, w in enumerate(weeks)]
    return {"commits": 717, "contributions": sum(map(sum, weeks)), "prs": 0, "current_streak": 5, "best_streak": 21,
            "top_lang": "Python", "days": days, "commit_weeks": [int(sum(w) * 0.8) for w in weeks],
            "updated": "sample data"}


def main():
    ASSETS.mkdir(exist_ok=True)
    if "--sample" in sys.argv:
        data = sample_data()
    else:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            sys.exit("Set GH_TOKEN (or run with --sample)")
        data = fetch_live(token)

    build_top()
    build_projects()
    build_stats(data)
    build_learning()
    build_footer()
    build_button("github", "GitHub", NAVY, CREAM, NAVY)
    build_button("linkedin", "LinkedIn", INK, CREAM, INK)
    build_button("instagram", "Instagram", CREAM, NAVY, NAVY)
    build_button("email", "Email", CREAM, NAVY, NAVY)
    build_button("repos", "View all repos", SUN, NAVY, NAVY)
    print("built:", ", ".join(sorted(p.name for p in ASSETS.glob("*.svg"))))


if __name__ == "__main__":
    main()
