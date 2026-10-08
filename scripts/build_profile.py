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
.num{{font-family:'Anton',sans-serif;font-size:78px;line-height:0.8;color:{NAVY};padding:6px 8px 0;display:inline-block}}
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
    <div class="sec"><span class="num" style="background:{SUN};border-radius:40% 55% 45% 60%">01</span><span class="t">Who am I?</span></div>
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
    <div class="sec"><span class="num" style="background:{SUN};border-radius:55% 40% 60% 45%">02</span><span class="t">Currently building</span></div>
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
  <div class="sec"><span class="num" style="color:{SUN};padding-left:0">03</span><span class="t" style="color:{SUN}">What I build</span><span class="marker" style="margin-left:auto;font-size:22px;color:{SUN}">~ ride the data wave</span></div>
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
  <div class="sec"><span class="num" style="background:{CREAM};border-radius:45% 60% 40% 55%">04</span><span class="t">Featured projects</span>
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
        <svg {SVGNS} width="100" height="12" viewBox="0 0 100 12" fill="none"><path d="M2 6 C 12 0, 22 12, 32 6 S 52 0, 62 6 S 82 12, 98 6" stroke="#E3DCC5" stroke-width="4" stroke-linecap="round"/><path d="M2 6 C 12 0, 22 12, 32 6 S 52 0, 62 6 S 82 12, 98 6" stroke="{INK}" stroke-width="4" stroke-linecap="round" stroke-dasharray="{done:.0f} 999"/></svg>
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
    weeks = data["weeks"]  # list of 7-day count lists, oldest first
    contrib_week = [sum(w) for w in weeks]
    commit_week = data["commit_weeks"]
    cw = 788
    peak = max(max(contrib_week), max(commit_week), 1)
    scaled_c = [v / peak for v in contrib_week]
    scaled_m = [v / peak for v in commit_week]

    # both lines share one scale
    def scaled_path(vals):
        pts = [(i * cw / (len(vals) - 1), 104 - v * 96) for i, v in enumerate(vals)]
        d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            mx = (x0 + x1) / 2
            d += f" C{mx:.1f} {y0:.1f} {mx:.1f} {y1:.1f} {x1:.1f} {y1:.1f}"
        return d
    line = scaled_path(scaled_c)
    line2 = scaled_path(scaled_m)
    area = line + f" L{cw} 112 L0 112 Z"

    # shade by quartiles of the distinct daily counts, so quiet 1-commit days and busy days look different
    levels = sorted({c for w in weeks for c in w if c > 0}) or [1]
    q = lambda p: levels[min(len(levels) - 1, int(p * len(levels)))]
    cuts = [q(0.25), q(0.5), q(0.75)] if len(levels) >= 4 else levels[:-1] + [10 ** 9] * (4 - len(levels))
    shades = ["#E7E0C8", "#B9C3F0", "#7D8FE6", "#3D57D4", INK]

    def shade(c):
        if c == 0:
            return shades[0]
        return shades[1 + sum(c > t for t in cuts)]

    ncols = len(weeks)
    cells = []
    for r in range(7):
        for c in range(ncols):
            v = weeks[c][r] if r < len(weeks[c]) else None
            cells.append(f'<span style="width:100%;aspect-ratio:1/1;border-radius:50%;background:{"transparent" if v is None else shade(v)}"></span>')

    updated = data["updated"]
    body = f"""
<div style="padding:30px 36px 20px;display:grid;grid-template-columns:1fr 1fr;gap:34px;position:relative">
  <div style="display:flex;flex-direction:column;gap:16px">
    <div class="sec"><span class="num" style="background:{CREAM};border-radius:60% 40% 55% 45%">05</span><span class="t">Tech stack</span></div>
    <div style="display:flex;flex-wrap:wrap;gap:8px">{stack}</div>
    <div class="marker" style="font-size:17px;color:{INK};transform:rotate(-2deg)">&#8627; the boards in my quiver</div>
  </div>
  <div style="display:flex;flex-direction:column;gap:16px">
    <div class="sec"><span class="num" style="background:{CREAM};border-radius:45% 55% 40% 60%">06</span><span class="t">Swell report</span>
      <span class="spin-slow" style="display:inline-block;width:30px;height:30px;margin-bottom:30px">{star(ORANGE, 30)}</span></div>
    <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px">
      <div style="background:{INK};color:{CREAM};border-radius:50% 50% 18px 18px;padding:18px 6px 14px;text-align:center"><div class="anton" style="font-size:38px;color:{SUN}">{data['commits']}</div><div class="mono" style="font-size:10.5px">COMMITS<br/>LAST YEAR</div></div>
      <div style="background:{SUN};border:2.5px solid {NAVY};border-radius:50% 50% 18px 18px;padding:16px 6px 12px;text-align:center"><div class="anton" style="font-size:38px">{data['current_streak']}<span style="font-size:18px"> d</span></div><div class="mono" style="font-size:10.5px">CURRENT<br/>STREAK</div></div>
      <div style="background:{CREAM};border:2.5px solid {NAVY};border-radius:50% 50% 18px 18px;padding:16px 6px 12px;text-align:center"><div class="anton" style="font-size:38px;color:{INK}">{data['best_streak']}<span style="font-size:18px"> d</span></div><div class="mono" style="font-size:10.5px">BEST<br/>STREAK</div></div>
    </div>
    <div class="mono" style="display:flex;justify-content:space-between;font-size:11.5px;border-top:2px solid {NAVY};padding-top:10px">
      <span>CONTRIBS &#183; {data['contributions']}</span><span>PRs &#183; {data['prs']}</span><span>TOP LANG &#183; {data['top_lang']}</span></div>
    <div class="marker" style="font-size:14px;color:{INK}">auto-refreshed &#183; {updated}</div>
  </div>
</div>
<div style="margin:6px 36px 0;border:2.5px solid {NAVY};border-radius:28px 20px 34px 22px;background:{CREAM};padding:20px 22px;display:flex;flex-direction:column;gap:12px;position:relative">
  <div style="display:flex;justify-content:space-between;align-items:center"><span class="anton" style="font-size:24px;color:{INK}">Tide chart &#183; commits &amp; contributions</span><span class="mono" style="font-size:11px">{ncols} WEEKS &#8594; TODAY</span></div>
  <svg {SVGNS} width="{cw}" height="112" viewBox="0 0 {cw} 112" fill="none">
    <path d="{area}" fill="{INK}" opacity="0.16"/>
    <path d="{line}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>
    <path class="march" d="{line2}" stroke="{ORANGE}" stroke-width="2.2" stroke-dasharray="5 5"/>
  </svg>
  <div style="display:grid;grid-template-columns:repeat({ncols},minmax(0,1fr));gap:3px">{''.join(cells)}</div>
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
        f'<path d="M3 7 C 20 1, 37 13, 55 7 S 92 1, 110 7 S 147 13, 165 7 S 200 1, 217 7" stroke="{INK}" stroke-width="6" stroke-linecap="round" stroke-dasharray="{L * f:.0f} 999"/></svg></div>'
        for n, f in LEARNING)
    body = f"""
<div style="padding:30px 36px 0;display:grid;grid-template-columns:1fr 1fr;gap:34px;position:relative;height:100%;background:{SUN}">
  <div style="display:flex;flex-direction:column;gap:14px">
    <div class="sec"><span class="num" style="padding-left:0">07</span><span class="t" style="font-size:32px">Currently learning</span></div>
    {rows}
    <div class="marker" style="font-size:17px;transform:rotate(-3deg);margin-top:4px">"a little progress each day."</div>
  </div>
  <div style="display:flex;flex-direction:column;gap:16px;position:relative">
    <div class="sec"><span class="num" style="padding-left:0">08</span><span class="t" style="font-size:32px">Let's connect</span></div>
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
STATS_H = 724
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
    weeks = [[d["contributionCount"] for d in w["contributionDays"]] for w in cc["contributionCalendar"]["weeks"]]
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
    days = sorted((k, v) for k, v in all_days.items() if k <= today)
    current, best = streaks(days)

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
        "weeks": weeks, "commit_weeks": commit_weeks,
        "updated": now.strftime("%d %b %Y, %H:%M UTC"),
    }


def sample_data():
    rnd = random.Random(7)
    weeks = []
    for i in range(53):
        wave = 0.5 + 0.5 * math.sin(i / 4.2)
        weeks.append([max(0, int(rnd.random() * 6 * wave + rnd.random() * 2 - 0.6)) for _ in range(7)])
    weeks[-1] = weeks[-1][:4]
    return {"commits": 717, "contributions": sum(map(sum, weeks)), "prs": 0, "current_streak": 5, "best_streak": 21,
            "top_lang": "Python", "weeks": weeks, "commit_weeks": [int(sum(w) * 0.8) for w in weeks],
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
