#!/usr/bin/env python3
"""Build the documentation SVG mockups.

Why a build script? The vendor file-write tool used to author this repo
truncates multi-byte UTF-8 characters (it keeps only the last byte),
which corrupts every emoji/dash/arrow we use in SVG text nodes. By
generating the files from this Python source (pure ASCII, with
\\uXXXX escapes for every non-ASCII character) and writing them via
Python's own UTF-8 file IO, we guarantee well-formed UTF-8 output.

Run:

    python3 scripts/build_docs_images.py

It writes 14 SVG files into docs/images/. They are static mockups
(approximations of the React admin console) used as screenshots in
README.md, USAGE.md and docs/*.md.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Output dir
# ---------------------------------------------------------------------------
OUT = Path(__file__).resolve().parent.parent / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------
FONT_FAMILY = (
    "Inter, ui-sans-serif, system-ui, -apple-system, "
    "'Segoe UI', Roboto, sans-serif"
)
MONO_FAMILY = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# Unicode characters used inside text nodes
NBSP = "\u00a0"
MIDDOT = "\u00b7"        # \u00B7
RARROW = "\u2192"        # \u2192
LRARROW = "\u2194"       # \u2194
EMDASH = "\u2014"        # \u2014
ENDASH = "\u2013"        # \u2013
GTE = "\u2265"           # \u2265
ELLIPSIS = "\u2026"      # \u2026
LDQUO = "\u201c"
RDQUO = "\u201d"
LSQUO = "\u2018"
RSQUO = "\u2019"
CHECK = "\u2713"
CROSS = "\u2715"
SEARCH = "\U0001F50D"
GLOBE = "\U0001F310"
FLAG_BR = "\U0001F1E7\U0001F1F7"
FLAG_GR = "\U0001F1EC\U0001F1F7"
ROBOT = "\U0001F916"
LAUGH = "\U0001F602"
SALAD = "\U0001F957"
SAT = "\U0001F4E1"
PHONE = "\U0001F4F1"
GEAR = "\u2699"
SCROLL = "\U0001F4DC"
GREEN_DOT = "\u25CF"
NOTE_PAD = "\U0001F4DD"
PLUS_HEAVY = "\u2795"
SUN = "\u2600"
MOON = "\u263E"
LOCK_SOLID = "\U0001F512"
KEY = "\U0001F511"
ENVELOPE = "\u2709"
CHART = "\U0001F4CA"
DATABASE = "\U0001F5C4"
CHECK_BOX = "\u2611"


def write_svg(filename: str, content: str) -> Path:
    """Write a UTF-8 SVG and validate it parses."""
    path = OUT / filename
    path.write_text(content, encoding="utf-8")
    try:
        ET.fromstring(path.read_bytes())
    except ET.ParseError as e:
        print(f"INVALID XML in {filename}: {e}", file=sys.stderr)
        raise
    return path


# ---------------------------------------------------------------------------
# Shared SVG building blocks
# ---------------------------------------------------------------------------
def shell_defs() -> str:
    return f"""
  <defs>
    <linearGradient id="brand" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#22c55e"/>
      <stop offset="100%" stop-color="#16a34a"/>
    </linearGradient>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#fafafa"/>
      <stop offset="100%" stop-color="#f4f4f5"/>
    </linearGradient>
    <linearGradient id="bgDark" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0a0a0a"/>
      <stop offset="100%" stop-color="#111114"/>
    </linearGradient>
    <linearGradient id="card" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#fafafa"/>
    </linearGradient>
    <linearGradient id="cardDark" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1a1a1f"/>
      <stop offset="100%" stop-color="#15151a"/>
    </linearGradient>
    <filter id="cardShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="10" flood-color="#0f172a" flood-opacity="0.10"/>
    </filter>
    <filter id="cardShadowDark" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="6" stdDeviation="12" flood-color="#000000" flood-opacity="0.45"/>
    </filter>
    <filter id="modalShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="20" stdDeviation="30" flood-color="#0f172a" flood-opacity="0.30"/>
    </filter>
  </defs>
"""


def app_shell(width: int, height: int, *, dark: bool, title: str, subtitle: str) -> str:
    """Render the left-rail sidebar + top bar of the admin console."""
    bg = "url(#bgDark)" if dark else "url(#bg)"
    side_bg = "#0c0c10" if dark else "#0a0a0a"
    side_text = "#a1a1aa" if dark else "#a1a1aa"
    side_active_bg = "#16a34a"
    side_active_fg = "white"
    top_bg = "#15151a" if dark else "white"
    top_border = "#27272a" if dark else "#e4e4e7"
    title_color = "#f4f4f5" if dark else "#18181b"
    sub_color = "#a1a1aa" if dark else "#71717a"

    items = [
        ("Dashboard", True),
        ("Chats", False),
        ("Bots", False),
        ("Diagnostics", False),
        ("Settings", False),
    ]
    nav_items = []
    for i, (label, active) in enumerate(items):
        y = 110 + i * 44
        if active:
            nav_items.append(
                f'<rect x="14" y="{y}" width="200" height="36" rx="9" fill="{side_active_bg}"/>'
                f'<text x="34" y="{y+22}" font-size="13" font-weight="600" fill="{side_active_fg}">{label}</text>'
            )
        else:
            nav_items.append(
                f'<text x="34" y="{y+22}" font-size="13" fill="{side_text}">{label}</text>'
            )
    nav = "\n      ".join(nav_items)

    return f"""
  <rect width="{width}" height="{height}" fill="{bg}"/>

  <!-- Sidebar -->
  <g>
    <rect width="228" height="{height}" fill="{side_bg}"/>
    <g transform="translate(28,40)">
      <rect width="32" height="32" rx="9" fill="url(#brand)"/>
      <text x="16" y="22" text-anchor="middle" font-size="14" font-weight="700" fill="white">W</text>
      <text x="44" y="22" font-size="15" font-weight="700" fill="white">Whatslang</text>
    </g>
    <text x="34" y="92" font-size="10" fill="#52525b" letter-spacing="1.4">NAVIGATION</text>
    <g>
      {nav}
    </g>
    <g transform="translate(28,{height-72})">
      <rect width="172" height="40" rx="10" fill="#15151a"/>
      <circle cx="24" cy="20" r="11" fill="#27272a"/>
      <text x="24" y="24" text-anchor="middle" font-size="11" font-weight="700" fill="#a1a1aa">A</text>
      <text x="44" y="17" font-size="11" font-weight="600" fill="#e4e4e7">admin</text>
      <text x="44" y="30" font-size="9" fill="#71717a">signed in</text>
    </g>
  </g>

  <!-- Top bar -->
  <g>
    <rect x="228" width="{width-228}" height="64" fill="{top_bg}"/>
    <line x1="228" y1="64" x2="{width}" y2="64" stroke="{top_border}"/>
    <g transform="translate(252,22)">
      <text font-size="16" font-weight="700" fill="{title_color}">{title}</text>
      <text y="20" font-size="11" fill="{sub_color}">{subtitle}</text>
    </g>
    <g transform="translate({width-300},20)">
      <rect width="120" height="28" rx="8" fill="{('#27272a' if dark else '#f4f4f5')}"/>
      <text x="14" y="18" font-size="11" fill="{sub_color}">Sync from WhatsApp</text>
    </g>
    <g transform="translate({width-160},20)">
      <rect width="100" height="28" rx="8" fill="url(#brand)"/>
      <text x="50" y="18" text-anchor="middle" font-size="11" font-weight="600" fill="white">+ Add chat</text>
    </g>
  </g>
"""


# ---------------------------------------------------------------------------
# Hero banner
# ---------------------------------------------------------------------------
def build_hero() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 480" font-family="{FONT_FAMILY}">
  <defs>
    <linearGradient id="hbg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#052e16"/>
      <stop offset="55%" stop-color="#064e3b"/>
      <stop offset="100%" stop-color="#0c0a09"/>
    </linearGradient>
    <linearGradient id="brand" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#22c55e"/>
      <stop offset="100%" stop-color="#16a34a"/>
    </linearGradient>
    <radialGradient id="hglow" cx="80%" cy="20%" r="60%">
      <stop offset="0%" stop-color="#22c55e" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="#22c55e" stop-opacity="0"/>
    </radialGradient>
    <filter id="cardShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="20" stdDeviation="30" flood-color="#000000" flood-opacity="0.45"/>
    </filter>
  </defs>

  <rect width="1280" height="480" fill="url(#hbg)"/>
  <rect width="1280" height="480" fill="url(#hglow)"/>

  <!-- Left: branding + tagline -->
  <g transform="translate(80,110)">
    <g>
      <rect width="60" height="60" rx="16" fill="url(#brand)"/>
      <text x="30" y="40" text-anchor="middle" font-size="28" font-weight="800" fill="white">W</text>
    </g>
    <text x="80" y="40" font-size="40" font-weight="800" fill="white">Whatslang</text>
    <text y="92" font-size="15" fill="#86efac" letter-spacing="2">MODULAR &#8226; MULTIMODAL &#8226; OPEN</text>
    <text y="148" font-size="22" font-weight="600" fill="#f0fdf4">Modular WhatsApp bots</text>
    <text y="178" font-size="22" font-weight="600" fill="#f0fdf4">with a sleek admin console.</text>
    <text y="220" font-size="13" fill="#bbf7d0">Declarative bot specs &#183; per-chat tuning &#183;</text>
    <text y="240" font-size="13" fill="#bbf7d0">multimodal LLM (text &#183; vision &#183; audio &#183; video)</text>
    <text y="260" font-size="13" fill="#bbf7d0">&#183; one container.</text>

    <g transform="translate(0,290)">
      <rect width="160" height="40" rx="10" fill="url(#brand)"/>
      <text x="80" y="26" text-anchor="middle" font-size="13" font-weight="700" fill="white">Get started</text>

      <rect x="176" width="140" height="40" rx="10" fill="none" stroke="#86efac"/>
      <text x="246" y="26" text-anchor="middle" font-size="13" font-weight="600" fill="#86efac">Read the docs</text>
    </g>
  </g>

  <!-- Right: stylised dashboard preview -->
  <g transform="translate(700,80)" filter="url(#cardShadow)">
    <rect width="500" height="320" rx="18" fill="#0a0a0a" stroke="#1f2937"/>
    <!-- Top bar -->
    <rect width="500" height="40" rx="18" fill="#111114"/>
    <rect y="18" width="500" height="22" fill="#111114"/>
    <circle cx="20" cy="20" r="5" fill="#ef4444"/>
    <circle cx="40" cy="20" r="5" fill="#f59e0b"/>
    <circle cx="60" cy="20" r="5" fill="#22c55e"/>
    <text x="250" y="25" text-anchor="middle" font-size="11" fill="#71717a">whatslang.app &#183; Dashboard</text>

    <!-- KPI row -->
    <g transform="translate(20,60)" font-family="{FONT_FAMILY}">
      <g>
        <rect width="100" height="64" rx="10" fill="#0c0c10" stroke="#1f2937"/>
        <text x="14" y="22" font-size="9" fill="#71717a">TOTAL CHATS</text>
        <text x="14" y="48" font-size="22" font-weight="700" fill="#22c55e">47</text>
      </g>
      <g transform="translate(112,0)">
        <rect width="100" height="64" rx="10" fill="#0c0c10" stroke="#1f2937"/>
        <text x="14" y="22" font-size="9" fill="#71717a">RUNNING BOTS</text>
        <text x="14" y="48" font-size="22" font-weight="700" fill="#86efac">8</text>
      </g>
      <g transform="translate(224,0)">
        <rect width="100" height="64" rx="10" fill="#0c0c10" stroke="#1f2937"/>
        <text x="14" y="22" font-size="9" fill="#71717a">BOT TYPES</text>
        <text x="14" y="48" font-size="22" font-weight="700" fill="#f4f4f5">4</text>
      </g>
      <g transform="translate(336,0)">
        <rect width="124" height="64" rx="10" fill="#0c0c10" stroke="#1f2937"/>
        <text x="14" y="22" font-size="9" fill="#71717a">ACTIVE 24H</text>
        <text x="14" y="48" font-size="22" font-weight="700" fill="#f4f4f5">12</text>
      </g>
    </g>

    <!-- Recent activity card -->
    <g transform="translate(20,148)">
      <rect width="460" height="148" rx="10" fill="#0c0c10" stroke="#1f2937"/>
      <text x="14" y="22" font-size="11" font-weight="700" fill="#e4e4e7">Recent activity</text>
      <g transform="translate(14,38)" font-size="10">
        <text fill="#22c55e">[ai]</text>
        <text x="34" fill="#a1a1aa">Friends &#183; Translated to PT</text>
        <text x="430" text-anchor="end" fill="#52525b">2m</text>

        <text y="22" fill="#22c55e">[health]</text>
        <text x="56" y="22" fill="#a1a1aa">DM Alex &#183; 480 kcal estimate</text>
        <text x="430" y="22" text-anchor="end" fill="#52525b">5m</text>

        <text y="44" fill="#22c55e">[joke]</text>
        <text x="42" y="44" fill="#a1a1aa">Family group &#183; pun about coffee</text>
        <text x="430" y="44" text-anchor="end" fill="#52525b">12m</text>

        <text y="66" fill="#22c55e">[tri]</text>
        <text x="34" y="66" fill="#a1a1aa">Greek travel &#183; EN/PT/EL output</text>
        <text x="430" y="66" text-anchor="end" fill="#52525b">22m</text>
      </g>
    </g>
  </g>

  <text x="80" y="448" font-size="11" fill="#52525b">FastAPI &#183; React &#183; SQLite &#183; Tailwind &#183; Docker &#183; MIT licence</text>
</svg>
"""


# ---------------------------------------------------------------------------
# Dashboard (light)
# ---------------------------------------------------------------------------
def _dashboard(dark: bool) -> str:
    bg = "url(#bgDark)" if dark else "url(#bg)"
    card = "url(#cardDark)" if dark else "url(#card)"
    border = "#27272a" if dark else "#e4e4e7"
    text = "#f4f4f5" if dark else "#18181b"
    sub = "#a1a1aa" if dark else "#71717a"
    soft = "#27272a" if dark else "#f4f4f5"
    shadow = "url(#cardShadowDark)" if dark else "url(#cardShadow)"

    kpis = [
        ("TOTAL CHATS", "47", "+4 this week"),
        ("RUNNING BOTS", "8", "across 6 chats"),
        ("BOT TYPES", "4", "translation, joke, ..."),
        ("ACTIVE 24H", "12", "of 47 chats"),
    ]
    kpi_blocks = []
    for i, (k, v, sub_t) in enumerate(kpis):
        x = i * 220
        kpi_blocks.append(f"""
      <g transform="translate({x},0)" filter="{shadow}">
        <rect width="200" height="92" rx="14" fill="{card}" stroke="{border}"/>
        <text x="20" y="26" font-size="10" font-weight="600" fill="{sub}" letter-spacing="1">{k}</text>
        <text x="20" y="60" font-size="28" font-weight="700" fill="{'#22c55e' if i in (0,1) else text}">{v}</text>
        <text x="20" y="80" font-size="10" fill="{sub}">{sub_t}</text>
      </g>""")
    kpi_row = "".join(kpi_blocks)

    activity = [
        ("[ai]",     "Friends",         f"Translated greeting to PT",                   "2m ago"),
        ("[health]", "DM Alex",         f"Estimated 480 kcal in lunch photo",           "5m ago"),
        ("[joke]",   "Family group",    f"Replied with a coffee pun",                   "12m ago"),
        ("[tri]",    "Greek travel",    f"EN {RARROW} PT + EL output for itinerary",   "22m ago"),
        ("[ai]",     "Work group",      f"OCRed sign in photo, translated EN {RARROW} PT", "44m ago"),
        ("[health]", "DM Sam",          f"Voice note transcribed, suggested a walk",    "1h ago"),
    ]
    rows = []
    for i, (prefix, chat, msg, when) in enumerate(activity):
        y = i * 36
        rows.append(f"""
        <g transform="translate(0,{y})">
          <rect width="624" height="32" rx="8" fill="{soft}" opacity="0.5"/>
          <text x="14" y="20" font-size="11" font-weight="700" fill="#22c55e" font-family="{MONO_FAMILY}">{prefix}</text>
          <text x="64" y="20" font-size="11" font-weight="600" fill="{text}">{chat}</text>
          <text x="160" y="20" font-size="11" fill="{sub}">{msg}</text>
          <text x="610" y="20" text-anchor="end" font-size="10" fill="{sub}">{when}</text>
        </g>""")
    activity_rows = "".join(rows)

    bot_cards = [
        (GLOBE, "EN {a} PT Translator", "[ai]", "running 4h 12m"),
        (FLAG_BR + FLAG_GR, "Trilingual EN {a} PT + EL", "[tri]", "running 1h 38m"),
        (LAUGH, "Joke Bot", "[joke]", "running 12m"),
        (SALAD, "Health Coach", "[health]", "running 22m"),
    ]
    bot_blocks = []
    for i, (emo, name, prefix, status) in enumerate(bot_cards):
        y = i * 60
        bot_blocks.append(f"""
        <g transform="translate(0,{y})">
          <rect width="316" height="52" rx="10" fill="{soft}" opacity="0.5"/>
          <text x="14" y="30" font-size="18">{emo}</text>
          <text x="60" y="22" font-size="12" font-weight="600" fill="{text}">{name.format(a=LRARROW)}</text>
          <text x="60" y="38" font-size="10" font-family="{MONO_FAMILY}" fill="#22c55e">{prefix}</text>
          <circle cx="290" cy="20" r="4" fill="#22c55e"/>
          <text x="298" y="24" text-anchor="end" font-size="10" fill="{sub}">{status}</text>
        </g>""")
    bot_rows = "".join(bot_blocks)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" font-family="{FONT_FAMILY}">
  {shell_defs()}
  {app_shell(1440, 900, dark=dark, title='Dashboard', subtitle=f'Overview of chats, bots and activity')}

  <!-- KPI row -->
  <g transform="translate(252,96)">
    {kpi_row}
  </g>

  <!-- Recent activity -->
  <g transform="translate(252,212)" filter="{shadow}">
    <rect width="652" height="316" rx="14" fill="{card}" stroke="{border}"/>
    <g transform="translate(20,24)">
      <text font-size="13" font-weight="700" fill="{text}">Recent activity</text>
      <text y="18" font-size="10" fill="{sub}">last 24 hours &#183; auto-refreshing</text>
    </g>
    <g transform="translate(20,68)">
      {activity_rows}
    </g>
  </g>

  <!-- Active bots -->
  <g transform="translate(924,212)" filter="{shadow}">
    <rect width="344" height="316" rx="14" fill="{card}" stroke="{border}"/>
    <g transform="translate(20,24)">
      <text font-size="13" font-weight="700" fill="{text}">Active bots</text>
      <text y="18" font-size="10" fill="{sub}">{4} running &#183; tap to manage</text>
    </g>
    <g transform="translate(14,68)">
      {bot_rows}
    </g>
  </g>

  <!-- Footer hint -->
  <text x="252" y="864" font-size="10" fill="{sub}">v1.0 &#183; FastAPI {EMDASH} React &#183; SQLite at /data/messages.db</text>
</svg>
"""


# ---------------------------------------------------------------------------
# Chats list
# ---------------------------------------------------------------------------
def build_chats() -> str:
    rows_data = [
        (CHECK_BOX, "Friends", "12345...whatsapp.net", "DM",      "421",  "2m ago",   2, True),
        (CHECK_BOX, "Greek travel", "67890...g.us",   "Group",   "1.2k", "22m ago",  1, True),
        ("",        "Family group", "11122...g.us",   "Group",   "812",  "12m ago",  1, True),
        ("",        "Work group", "33445...g.us",     "Group",   "643",  "44m ago",  1, True),
        ("",        "DM Alex", "55566...whatsapp.net", "DM",      "203",  "5m ago",   2, True),
        ("",        "DM Sam", "77788...whatsapp.net",  "DM",      "118",  "1h ago",   1, True),
        ("",        "Mom", "99900...whatsapp.net",     "DM",      "67",   "yesterday", 0, False),
        ("",        "Project Phoenix", "10203...g.us", "Group",   "412",  "3h ago",    0, False),
        ("",        "Yoga class", "20304...g.us",      "Group",   "89",   "yesterday", 0, False),
        ("",        "Old colleagues", "30405...g.us",  "Group",   "23",   "5d ago",    0, False),
    ]
    rows = []
    for i, (chk, name, jid, kind, count, when, bots, active) in enumerate(rows_data):
        y = i * 44
        chk_fill = "#16a34a" if chk else "white"
        chk_glyph = '<path d="M5 9 L8 12 L13 7" stroke="white" stroke-width="2" fill="none"/>' if chk else ""
        bot_chip = ""
        if bots > 0:
            bot_chip = (
                f'<rect x="0" y="0" width="48" height="20" rx="10" fill="#dcfce7"/>'
                f'<text x="24" y="14" text-anchor="middle" font-size="10" font-weight="600" fill="#166534">{bots} bot{"" if bots==1 else "s"}</text>'
            )
        else:
            bot_chip = (
                f'<rect x="0" y="0" width="48" height="20" rx="10" fill="#f4f4f5"/>'
                f'<text x="24" y="14" text-anchor="middle" font-size="10" font-weight="600" fill="#71717a">none</text>'
            )
        kind_chip_color = "#dbeafe" if kind == "Group" else "#fef3c7"
        kind_chip_text = "#1e40af" if kind == "Group" else "#92400e"
        rows.append(f"""
        <g transform="translate(0,{y})">
          <rect width="1100" height="40" rx="10" fill="{'#fafafa' if i%2 else 'white'}"/>
          <g transform="translate(16,12)">
            <rect width="16" height="16" rx="4" fill="{chk_fill}" stroke="#16a34a"/>
            {chk_glyph}
          </g>
          <text x="48" y="26" font-size="12" font-weight="600" fill="#18181b">{name}</text>
          <text x="48" y="40" font-size="10" font-family="{MONO_FAMILY}" fill="#a1a1aa" opacity="0.0">{jid}</text>

          <g transform="translate(280,10)">
            <rect width="56" height="20" rx="10" fill="{kind_chip_color}"/>
            <text x="28" y="14" text-anchor="middle" font-size="10" font-weight="600" fill="{kind_chip_text}">{kind}</text>
          </g>

          <text x="408" y="26" font-size="12" fill="#52525b">{count}</text>
          <text x="528" y="26" font-size="12" fill="#52525b">{when}</text>

          <g transform="translate(700,10)">
            {bot_chip}
          </g>

          <g transform="translate(800,10)">
            <circle cx="6" cy="10" r="4" fill="{'#22c55e' if active else '#a1a1aa'}"/>
            <text x="20" y="14" font-size="11" fill="#52525b">{'Active' if active else 'Quiet'}</text>
          </g>

          <g transform="translate(940,8)">
            <rect width="60" height="24" rx="6" fill="#f4f4f5"/>
            <text x="30" y="16" text-anchor="middle" font-size="10" font-weight="600" fill="#52525b">Open</text>
            <rect x="68" width="80" height="24" rx="6" fill="#fee2e2"/>
            <text x="108" y="16" text-anchor="middle" font-size="10" font-weight="600" fill="#b91c1c">Stop bots</text>
          </g>
        </g>""")
    rows_svg = "".join(rows)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" font-family="{FONT_FAMILY}">
  {shell_defs()}
  {app_shell(1440, 900, dark=False, title='Chats', subtitle='47 chats &#183; 8 bots running &#183; sorted by latest message')}

  <!-- Filters bar -->
  <g transform="translate(252,96)" filter="url(#cardShadow)">
    <rect width="1140" height="60" rx="14" fill="white" stroke="#e4e4e7"/>
    <g transform="translate(20,16)">
      <rect width="320" height="28" rx="8" fill="#f4f4f5"/>
      <text x="14" y="18" font-size="12" fill="#a1a1aa">Search by name or JID{ELLIPSIS}</text>
    </g>
    <g transform="translate(360,16)" font-size="11">
      <rect width="92" height="28" rx="8" fill="#f0fdf4" stroke="#bbf7d0"/>
      <text x="46" y="18" text-anchor="middle" font-weight="600" fill="#166534">Type: any</text>
    </g>
    <g transform="translate(464,16)" font-size="11">
      <rect width="120" height="28" rx="8" fill="#f0fdf4" stroke="#bbf7d0"/>
      <text x="60" y="18" text-anchor="middle" font-weight="600" fill="#166534">Activity: active</text>
    </g>
    <g transform="translate(596,16)" font-size="11">
      <rect width="148" height="28" rx="8" fill="#f0fdf4" stroke="#bbf7d0"/>
      <text x="74" y="18" text-anchor="middle" font-weight="600" fill="#166534">Bot status: running</text>
    </g>
    <g transform="translate(940,16)" font-size="11">
      <rect width="84" height="28" rx="8" fill="#f4f4f5"/>
      <text x="42" y="18" text-anchor="middle" font-weight="600" fill="#52525b">20 / page</text>
    </g>
    <g transform="translate(1036,16)" font-size="11">
      <rect width="84" height="28" rx="8" fill="url(#brand)"/>
      <text x="42" y="18" text-anchor="middle" font-weight="600" fill="white">Apply</text>
    </g>
  </g>

  <!-- Bulk action bar -->
  <g transform="translate(252,168)">
    <rect width="1140" height="44" rx="10" fill="#fffbeb" stroke="#fde68a"/>
    <text x="20" y="28" font-size="12" font-weight="600" fill="#92400e">2 chats selected</text>
    <g transform="translate(220,10)" font-size="11">
      <rect width="92" height="24" rx="6" fill="#dcfce7"/>
      <text x="46" y="16" text-anchor="middle" font-weight="600" fill="#166534">Start bots</text>
      <rect x="100" width="92" height="24" rx="6" fill="#fee2e2"/>
      <text x="146" y="16" text-anchor="middle" font-weight="600" fill="#b91c1c">Stop bots</text>
      <rect x="200" width="92" height="24" rx="6" fill="#f4f4f5"/>
      <text x="246" y="16" text-anchor="middle" font-weight="600" fill="#52525b">Delete</text>
    </g>
    <text x="1116" y="28" text-anchor="end" font-size="11" fill="#92400e">Clear selection</text>
  </g>

  <!-- Table -->
  <g transform="translate(252,224)" filter="url(#cardShadow)">
    <rect width="1140" height="616" rx="14" fill="white" stroke="#e4e4e7"/>
    <!-- Header row -->
    <g transform="translate(0,0)">
      <rect width="1140" height="40" rx="14" fill="#fafafa"/>
      <rect y="20" width="1140" height="20" fill="#fafafa"/>
      <line x1="0" y1="40" x2="1140" y2="40" stroke="#e4e4e7"/>
      <text x="48" y="26" font-size="10" font-weight="700" fill="#71717a" letter-spacing="1">CHAT</text>
      <text x="280" y="26" font-size="10" font-weight="700" fill="#71717a" letter-spacing="1">TYPE</text>
      <text x="408" y="26" font-size="10" font-weight="700" fill="#71717a" letter-spacing="1">MESSAGES</text>
      <text x="528" y="26" font-size="10" font-weight="700" fill="#71717a" letter-spacing="1">LATEST</text>
      <text x="700" y="26" font-size="10" font-weight="700" fill="#71717a" letter-spacing="1">BOTS</text>
      <text x="800" y="26" font-size="10" font-weight="700" fill="#71717a" letter-spacing="1">STATUS</text>
      <text x="940" y="26" font-size="10" font-weight="700" fill="#71717a" letter-spacing="1">ACTIONS</text>
    </g>
    <g transform="translate(0,48)">
      {rows_svg}
    </g>

    <!-- Pagination footer -->
    <g transform="translate(0,572)">
      <line y1="0" x2="1140" y2="0" stroke="#f4f4f5"/>
      <text x="20" y="28" font-size="11" fill="#71717a">Showing 1{ENDASH}10 of 47</text>
      <g transform="translate(900,8)" font-size="11">
        <rect width="36" height="24" rx="6" fill="#f4f4f5"/>
        <text x="18" y="16" text-anchor="middle" fill="#52525b">{LRARROW}</text>
        <rect x="44" width="28" height="24" rx="6" fill="#16a34a"/>
        <text x="58" y="16" text-anchor="middle" fill="white" font-weight="700">1</text>
        <rect x="80" width="28" height="24" rx="6" fill="#f4f4f5"/>
        <text x="94" y="16" text-anchor="middle" fill="#52525b">2</text>
        <rect x="116" width="28" height="24" rx="6" fill="#f4f4f5"/>
        <text x="130" y="16" text-anchor="middle" fill="#52525b">3</text>
        <rect x="152" width="36" height="24" rx="6" fill="#f4f4f5"/>
        <text x="170" y="16" text-anchor="middle" fill="#52525b">{RARROW}</text>
      </g>
    </g>
  </g>
</svg>
"""


# ---------------------------------------------------------------------------
# Chat detail
# ---------------------------------------------------------------------------
def build_chat_detail() -> str:
    bot_rows = [
        (GLOBE, "EN {a} PT Translator".format(a=LRARROW), "[ai]", True, "running 4h 12m", "ctx 0  &#183;  redirect off"),
        (FLAG_BR+FLAG_GR, "Trilingual EN+PT+EL", "[tri]", True, "running 1h 38m", "ctx 5  &#183;  redirect off"),
        (LAUGH, "Joke Bot", "[joke]", False, "stopped",        "ctx 0  &#183;  redirect off"),
        (SALAD, "Health Coach", "[health]", False, "stopped",  "ctx 5  &#183;  redirect to DM Sam"),
    ]
    cards = []
    for i, (emo, name, prefix, running, status, sub) in enumerate(bot_rows):
        y = i * 110
        dot = "#22c55e" if running else "#a1a1aa"
        action_label = "Stop" if running else "Start"
        action_bg = "#fee2e2" if running else "#dcfce7"
        action_fg = "#b91c1c" if running else "#166534"
        cards.append(f"""
        <g transform="translate(0,{y})" filter="url(#cardShadow)">
          <rect width="724" height="98" rx="14" fill="white" stroke="#e4e4e7"/>
          <g transform="translate(20,16)">
            <text font-size="22">{emo}</text>
            <text x="44" y="6" font-size="14" font-weight="700" fill="#18181b">{name}</text>
            <text x="44" y="24" font-family="{MONO_FAMILY}" font-size="11" fill="#16a34a">{prefix}</text>
          </g>
          <g transform="translate(20,62)">
            <circle cx="6" cy="6" r="6" fill="{dot}"/>
            <text x="20" y="10" font-size="11" font-weight="600" fill="#27272a">{status}</text>
            <text x="20" y="26" font-size="10" fill="#71717a">{sub}</text>
          </g>
          <g transform="translate(540,30)">
            <rect width="56" height="28" rx="8" fill="#f4f4f5"/>
            <text x="28" y="18" text-anchor="middle" font-size="11" font-weight="600" fill="#52525b">{GEAR} Settings</text>
            <rect x="64" width="44" height="28" rx="8" fill="#f4f4f5"/>
            <text x="86" y="18" text-anchor="middle" font-size="11" font-weight="600" fill="#52525b">{SCROLL} Logs</text>
            <rect x="116" width="56" height="28" rx="8" fill="{action_bg}"/>
            <text x="144" y="18" text-anchor="middle" font-size="11" font-weight="700" fill="{action_fg}">{action_label}</text>
          </g>
        </g>""")
    bot_cards_svg = "".join(cards)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" font-family="{FONT_FAMILY}">
  {shell_defs()}
  {app_shell(1440, 900, dark=False, title='Friends', subtitle='12345...whatsapp.net &#183; DM &#183; 421 messages &#183; last 2 minutes ago')}

  <!-- Chat info -->
  <g transform="translate(252,96)" filter="url(#cardShadow)">
    <rect width="1140" height="100" rx="14" fill="white" stroke="#e4e4e7"/>
    <g transform="translate(28,26)">
      <circle cx="22" cy="22" r="22" fill="#dcfce7"/>
      <text x="22" y="29" text-anchor="middle" font-size="20" font-weight="700" fill="#166534">F</text>
      <text x="60" y="20" font-size="16" font-weight="700" fill="#18181b">Friends</text>
      <text x="60" y="40" font-size="11" fill="#71717a" font-family="{MONO_FAMILY}">12345.whatsapp.net</text>

      <g transform="translate(60,52)" font-size="10">
        <rect width="40" height="20" rx="10" fill="#fef3c7"/>
        <text x="20" y="14" text-anchor="middle" font-weight="600" fill="#92400e">DM</text>
        <text x="60" y="14" fill="#71717a">421 messages &#183; last activity 2 minutes ago</text>
      </g>
    </g>
    <g transform="translate(900,32)">
      <rect width="100" height="32" rx="8" fill="#f4f4f5"/>
      <text x="50" y="20" text-anchor="middle" font-size="11" font-weight="600" fill="#52525b">{ENVELOPE} Messages</text>
      <rect x="112" width="120" height="32" rx="8" fill="#fee2e2"/>
      <text x="172" y="20" text-anchor="middle" font-size="11" font-weight="700" fill="#b91c1c">Delete chat</text>
    </g>
  </g>

  <!-- Bot assignments -->
  <g transform="translate(252,212)">
    <text font-size="13" font-weight="700" fill="#18181b">Bot assignments</text>
    <text y="18" font-size="11" fill="#71717a">Toggle bots for this chat. Settings persist after stopping.</text>

    <g transform="translate(0,42)">
      {bot_cards_svg}
    </g>
  </g>

  <!-- Add a bot side panel -->
  <g transform="translate(996,212)" filter="url(#cardShadow)">
    <rect width="396" height="500" rx="14" fill="white" stroke="#e4e4e7"/>
    <g transform="translate(20,24)">
      <text font-size="13" font-weight="700" fill="#18181b">Add a bot</text>
      <text y="18" font-size="11" fill="#71717a">Pick from the catalog below to assign.</text>
    </g>

    <g transform="translate(20,68)">
      <rect width="356" height="36" rx="8" fill="#f4f4f5"/>
      <text x="14" y="22" font-size="11" fill="#a1a1aa">Search bots{ELLIPSIS}</text>
    </g>

    <g transform="translate(20,124)">
      <rect width="356" height="68" rx="10" fill="#f9fafb" stroke="#e4e4e7"/>
      <text x="14" y="22" font-size="18">{GLOBE}</text>
      <text x="44" y="22" font-size="12" font-weight="700" fill="#18181b">EN {LRARROW} PT Translator</text>
      <text x="14" y="42" font-size="10" fill="#71717a">[ai] &#183; text + image + audio + video</text>
      <text x="14" y="58" font-size="10" fill="#71717a">Translates English {LRARROW} Portuguese.</text>
      <g transform="translate(310,38)">
        <rect width="36" height="24" rx="6" fill="url(#brand)"/>
        <text x="18" y="16" text-anchor="middle" font-size="11" font-weight="700" fill="white">{RARROW}</text>
      </g>
    </g>

    <g transform="translate(20,208)">
      <rect width="356" height="68" rx="10" fill="#f9fafb" stroke="#e4e4e7"/>
      <text x="14" y="22" font-size="18">{LAUGH}</text>
      <text x="44" y="22" font-size="12" font-weight="700" fill="#18181b">Joke Bot</text>
      <text x="14" y="42" font-size="10" fill="#71717a">[joke] &#183; text only</text>
      <text x="14" y="58" font-size="10" fill="#71717a">Family-friendly joke per message.</text>
      <g transform="translate(310,38)">
        <rect width="36" height="24" rx="6" fill="url(#brand)"/>
        <text x="18" y="16" text-anchor="middle" font-size="11" font-weight="700" fill="white">{RARROW}</text>
      </g>
    </g>

    <g transform="translate(20,292)">
      <rect width="356" height="68" rx="10" fill="#f9fafb" stroke="#e4e4e7"/>
      <text x="14" y="22" font-size="18">{SALAD}</text>
      <text x="44" y="22" font-size="12" font-weight="700" fill="#18181b">Health Coach</text>
      <text x="14" y="42" font-size="10" fill="#71717a">[health] &#183; text + image + audio + video</text>
      <text x="14" y="58" font-size="10" fill="#71717a">Empathic but honest. Estimates kcal.</text>
      <g transform="translate(310,38)">
        <rect width="36" height="24" rx="6" fill="url(#brand)"/>
        <text x="18" y="16" text-anchor="middle" font-size="11" font-weight="700" fill="white">{RARROW}</text>
      </g>
    </g>

    <g transform="translate(20,376)">
      <rect width="356" height="68" rx="10" fill="#f9fafb" stroke="#e4e4e7"/>
      <text x="14" y="22" font-size="18">{FLAG_BR}{FLAG_GR}</text>
      <text x="60" y="22" font-size="12" font-weight="700" fill="#18181b">Trilingual EN/PT/EL</text>
      <text x="14" y="42" font-size="10" fill="#71717a">[tri] &#183; text + image + audio + video</text>
      <text x="14" y="58" font-size="10" fill="#71717a">EN {RARROW} PT+EL, anything else {RARROW} EN.</text>
      <g transform="translate(310,38)">
        <rect width="36" height="24" rx="6" fill="url(#brand)"/>
        <text x="18" y="16" text-anchor="middle" font-size="11" font-weight="700" fill="white">{RARROW}</text>
      </g>
    </g>
  </g>
</svg>
"""


# ---------------------------------------------------------------------------
# Bots catalog page
# ---------------------------------------------------------------------------
def build_bots_page() -> str:
    cards = [
        (GLOBE, "EN {a} PT Translator".format(a=LRARROW), "[ai]",
         "Translates between English and Portuguese. Detects source language. Handles text, OCR, voice, video.",
         ("text","image","audio","video")),
        (FLAG_BR+FLAG_GR, "Trilingual EN {a} PT + EL".format(a=LRARROW), "[tri]",
         "When EN: outputs PT-BR + Greek. Anything else: outputs English. Multimodal.",
         ("text","image","audio","video")),
        (LAUGH, "Joke Bot", "[joke]",
         "Replies with a short, family-friendly joke matching the user&#8217;s language.",
         ("text",)),
        (SALAD, "Health Coach", "[health]",
         "Empathic but honest. Estimates kcal &amp; macros from food photos. Transcribes voice notes.",
         ("text","image","audio","video")),
    ]
    chip_for = {
        "text":  ("#dbeafe", "#1e40af", "Text"),
        "image": ("#fde68a", "#92400e", "Image"),
        "audio": ("#fbcfe8", "#9d174d", "Audio"),
        "video": ("#ddd6fe", "#5b21b6", "Video"),
    }
    card_blocks = []
    for i, (emo, name, prefix, desc, modes) in enumerate(cards):
        col = i % 2
        row = i // 2
        x = col * 460
        y = row * 220
        chips = []
        for j, m in enumerate(modes):
            bg, fg, lbl = chip_for[m]
            chips.append(
                f'<g transform="translate({j*64},0)">'
                f'<rect width="56" height="22" rx="11" fill="{bg}"/>'
                f'<text x="28" y="15" text-anchor="middle" font-size="10" font-weight="600" fill="{fg}">{lbl}</text>'
                f'</g>'
            )
        chips_svg = "".join(chips)
        card_blocks.append(f"""
        <g transform="translate({x},{y})" filter="url(#cardShadow)">
          <rect width="436" height="200" rx="14" fill="white" stroke="#e4e4e7"/>
          <g transform="translate(24,24)">
            <text font-size="32">{emo}</text>
            <text x="56" y="6" font-size="15" font-weight="700" fill="#18181b">{name}</text>
            <text x="56" y="26" font-family="{MONO_FAMILY}" font-size="11" fill="#16a34a">{prefix}</text>
          </g>
          <text x="24" y="98" font-size="11" fill="#52525b">{desc[:60]}</text>
          <text x="24" y="114" font-size="11" fill="#52525b">{desc[60:120]}</text>
          <text x="24" y="130" font-size="11" fill="#52525b">{desc[120:]}</text>
          <g transform="translate(24,144)">
            {chips_svg}
          </g>
          <g transform="translate(304,158)">
            <rect width="108" height="28" rx="8" fill="#f4f4f5"/>
            <text x="54" y="18" text-anchor="middle" font-size="11" font-weight="600" fill="#52525b">Start {RARROW}</text>
          </g>
        </g>""")
    cards_svg = "".join(card_blocks)

    running = [
        (GLOBE, "[ai]", "Friends", "4h 12m"),
        (GLOBE, "[ai]", "Work group", "44m"),
        (FLAG_BR+FLAG_GR, "[tri]", "Greek travel", "1h 38m"),
        (LAUGH, "[joke]", "Family group", "12m"),
        (SALAD, "[health]", "DM Alex", "22m"),
    ]
    running_blocks = []
    for i, (emo, prefix, chat, uptime) in enumerate(running):
        y = i * 38
        running_blocks.append(f"""
        <g transform="translate(0,{y})">
          <rect width="320" height="32" rx="8" fill="#f9fafb"/>
          <text x="14" y="22" font-size="18">{emo}</text>
          <text x="44" y="20" font-size="11" font-family="{MONO_FAMILY}" fill="#16a34a">{prefix}</text>
          <text x="84" y="20" font-size="11" fill="#27272a">{chat}</text>
          <circle cx="270" cy="16" r="4" fill="#22c55e"/>
          <text x="306" y="20" text-anchor="end" font-size="10" fill="#71717a">{uptime}</text>
        </g>""")
    running_svg = "".join(running_blocks)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" font-family="{FONT_FAMILY}">
  {shell_defs()}
  {app_shell(1440, 900, dark=False, title='Bots', subtitle='4 bot types in catalog &#183; 8 instances running across 6 chats')}

  <!-- Currently running -->
  <g transform="translate(252,96)" filter="url(#cardShadow)">
    <rect width="350" height="316" rx="14" fill="white" stroke="#e4e4e7"/>
    <g transform="translate(20,24)">
      <text font-size="13" font-weight="700" fill="#18181b">Currently running</text>
      <text y="18" font-size="10" fill="#71717a">5 instances</text>
    </g>
    <g transform="translate(14,68)">
      {running_svg}
    </g>
  </g>

  <!-- Catalog cards -->
  <g transform="translate(620,96)">
    {cards_svg}
  </g>

  <text x="252" y="864" font-size="10" fill="#71717a">Add a new bot in app/bots/__init__.py and restart {ENDASH} it shows up here.</text>
</svg>
"""


# ---------------------------------------------------------------------------
# Settings modal
# ---------------------------------------------------------------------------
def build_bot_settings_modal() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" font-family="{FONT_FAMILY}">
  {shell_defs()}
  <rect width="1440" height="900" fill="#0f172a" fill-opacity="0.55"/>

  <g transform="translate(440,160)" filter="url(#modalShadow)">
    <rect width="560" height="580" rx="18" fill="white"/>
    <g transform="translate(28,28)">
      <text font-size="18" font-weight="700" fill="#18181b">Bot settings &#183; EN {LRARROW} PT Translator</text>
      <text y="22" font-size="12" fill="#71717a">Per-chat overrides for [ai] in &#8220;Friends&#8221;.</text>
    </g>
    <text x="528" y="42" text-anchor="end" font-size="20" fill="#a1a1aa">{CROSS}</text>
    <line x1="0" y1="80" x2="560" y2="80" stroke="#f4f4f5"/>

    <!-- Answer my own messages -->
    <g transform="translate(28,108)">
      <text font-size="13" font-weight="700" fill="#18181b">Answer my own messages</text>
      <text y="18" font-size="11" fill="#71717a">If on, the bot also responds to messages you send.</text>
      <g transform="translate(440,4)">
        <rect width="44" height="24" rx="12" fill="#22c55e"/>
        <circle cx="32" cy="12" r="9" fill="white"/>
      </g>
    </g>

    <line x1="28" y1="172" x2="532" y2="172" stroke="#f4f4f5"/>

    <!-- Conversation context -->
    <g transform="translate(28,196)">
      <text font-size="13" font-weight="700" fill="#18181b">Conversation context</text>
      <text y="18" font-size="11" fill="#71717a">Number of previous messages to include as history (0 = stateless).</text>
      <g transform="translate(360,2)">
        <rect width="32" height="28" rx="6" fill="#f4f4f5"/>
        <text x="16" y="20" text-anchor="middle" font-size="14" font-weight="700" fill="#52525b">{ENDASH}</text>
        <rect x="40" width="60" height="28" rx="6" fill="white" stroke="#22c55e"/>
        <text x="70" y="20" text-anchor="middle" font-size="14" font-weight="700" fill="#18181b">5</text>
        <rect x="108" width="32" height="28" rx="6" fill="#f4f4f5"/>
        <text x="124" y="20" text-anchor="middle" font-size="14" font-weight="700" fill="#52525b">+</text>
      </g>
    </g>

    <line x1="28" y1="270" x2="532" y2="270" stroke="#f4f4f5"/>

    <!-- Send replies to another chat -->
    <g transform="translate(28,294)">
      <text font-size="13" font-weight="700" fill="#18181b">Send replies to another chat</text>
      <text y="18" font-size="11" fill="#71717a">Optional. Forwards the original message and the bot{RSQUO}s reply.</text>

      <g transform="translate(0,40)">
        <rect width="500" height="38" rx="8" fill="white" stroke="#e4e4e7"/>
        <text x="14" y="24" font-size="12" fill="#a1a1aa">Pick a chat (start typing){ELLIPSIS}</text>
      </g>
      <g transform="translate(0,90)">
        <rect width="500" height="40" rx="10" fill="#fef3c7" opacity="0.6"/>
        <text x="14" y="20" font-size="11" font-weight="700" fill="#92400e">Currently:</text>
        <text x="84" y="20" font-size="11" fill="#92400e">none (replies go back to this chat)</text>
        <text x="486" y="26" text-anchor="end" font-size="10" font-weight="700" fill="#b91c1c">Clear</text>
      </g>
    </g>

    <line x1="28" y1="448" x2="532" y2="448" stroke="#f4f4f5"/>

    <!-- Footer -->
    <g transform="translate(28,476)">
      <text font-size="11" fill="#71717a">Changes apply on the next polling cycle ({MIDDOT} 5s).</text>
    </g>
    <g transform="translate(380,508)">
      <rect width="64" height="36" rx="8" fill="#f4f4f5"/>
      <text x="32" y="22" text-anchor="middle" font-size="12" font-weight="600" fill="#52525b">Cancel</text>
      <rect x="76" width="76" height="36" rx="8" fill="url(#brand)"/>
      <text x="114" y="22" text-anchor="middle" font-size="12" font-weight="700" fill="white">Save</text>
    </g>
  </g>
</svg>
"""


# ---------------------------------------------------------------------------
# Logs modal
# ---------------------------------------------------------------------------
def build_bot_logs_modal() -> str:
    log_lines = [
        ("INFO",  "16:42:08", "Bot translation starting for 12345...whatsapp.net"),
        ("INFO",  "16:42:13", "Polled 14 messages, 1 new"),
        ("INFO",  "16:42:13", "Calling LLM (gpt-4o-mini, history=5)"),
        ("INFO",  "16:42:14", "LLM responded in 942ms"),
        ("INFO",  "16:42:14", "Replied to ABCDEF12 (1 chunks)"),
        ("INFO",  "16:42:18", "Polled 15 messages, 0 new"),
        ("INFO",  "16:42:23", "Polled 15 messages, 1 new (image)"),
        ("INFO",  "16:42:23", "Downloaded image (245 KB)"),
        ("INFO",  "16:42:24", "Calling LLM with image (gpt-4o-mini)"),
        ("INFO",  "16:42:26", "LLM responded in 1843ms"),
        ("INFO",  "16:42:26", "Replied to GHIJKL34 (1 chunks)"),
        ("INFO",  "16:42:31", "Polled 16 messages, 1 new (audio)"),
        ("INFO",  "16:42:31", "Downloaded audio (32 KB)"),
        ("INFO",  "16:42:32", "Transcribing with whisper-1"),
        ("INFO",  "16:42:35", "Transcription: &#8220;Buenos d{LSQUO}ias amigo{RDQUO}".format(LSQUO=LSQUO, RDQUO=RDQUO)),
        ("INFO",  "16:42:35", "Calling LLM with transcript"),
        ("INFO",  "16:42:36", "LLM responded in 612ms"),
        ("INFO",  "16:42:36", "Replied to MNOPQR56 (1 chunks)"),
        ("WARN",  "16:42:41", "Gateway returned 502 on get_messages, will retry"),
        ("INFO",  "16:42:46", "Polled 17 messages, 0 new"),
    ]
    rows = []
    for i, (lvl, ts, msg) in enumerate(log_lines):
        y = i * 26
        lvl_color = "#22c55e" if lvl == "INFO" else "#f59e0b"
        rows.append(f"""
        <g transform="translate(0,{y})">
          <text x="0" y="14" font-family="{MONO_FAMILY}" font-size="10" fill="#a1a1aa">{ts}</text>
          <text x="80" y="14" font-family="{MONO_FAMILY}" font-size="10" font-weight="700" fill="{lvl_color}">{lvl}</text>
          <text x="120" y="14" font-family="{MONO_FAMILY}" font-size="10" fill="#27272a">{msg}</text>
        </g>""")
    rows_svg = "".join(rows)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" font-family="{FONT_FAMILY}">
  {shell_defs()}
  <rect width="1440" height="900" fill="#0f172a" fill-opacity="0.55"/>

  <g transform="translate(280,80)" filter="url(#modalShadow)">
    <rect width="880" height="740" rx="18" fill="white"/>
    <g transform="translate(28,28)">
      <text font-size="18" font-weight="700" fill="#18181b">Logs &#183; Trilingual EN {LRARROW} PT + EL</text>
      <text y="20" font-size="12" fill="#71717a">Most recent log lines (auto-refreshing every 2s)</text>
    </g>
    <text x="848" y="42" text-anchor="end" font-size="20" fill="#a1a1aa">{CROSS}</text>
    <line x1="0" y1="80" x2="880" y2="80" stroke="#f4f4f5"/>

    <g transform="translate(24,104)">
      <rect width="832" height="568" rx="10" fill="#0a0a0a"/>
      <g transform="translate(20,18)">
        {rows_svg}
      </g>
    </g>

    <g transform="translate(24,696)" font-size="11">
      <text fill="#71717a">Buffer: 200 lines &#183; chat 12345...whatsapp.net</text>
      <text x="800" text-anchor="end">
        <tspan fill="#71717a">Refreshing every 2s &#183; </tspan>
        <tspan fill="#16a34a" font-weight="700">live</tspan>
      </text>
    </g>
  </g>
</svg>
"""


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------
def build_diagnostics() -> str:
    panels_top = [
        ("WhatsApp gateway", [
            ("Base URL",       "http://wa-gateway:8081"),
            ("Reachable",      f"{CHECK} yes"),
            ("HTTP status",    "200 (38 ms)"),
            ("Logged in",      f"{CHECK} yes"),
            ("Device JID",     "12345...whatsapp.net"),
            ("Calls / errors", "12 483 / 0"),
        ], "#16a34a"),
        ("LLM provider", [
            ("Base URL",       "https://api.openai.com/v1"),
            ("Text model",     "gpt-4o-mini"),
            ("Vision model",   "gpt-4o-mini"),
            ("Audio model",    "whisper-1"),
            ("API key set",    f"{CHECK} yes"),
            ("Note",           "no live probe (saves $)"),
        ], "#0ea5e9"),
        ("Database", [
            ("Path",           "/data/messages.db"),
            ("Size",           "1.2 MiB"),
            ("Chats",          "47"),
            ("Assignments",    "12"),
            ("Processed msgs", "9 821"),
            ("WAL",            f"{CHECK} on"),
        ], "#a855f7"),
        ("Bot runtime", [
            ("Catalog size",   "4"),
            ("Running bots",   "8"),
            ("Poll interval",  "5 s"),
            ("Threads",        "8 alive"),
            ("Last error",     f"{EMDASH}"),
            ("Uptime",         "3 d 7 h"),
        ], "#f59e0b"),
    ]
    panel_blocks = []
    for i, (title, rows, accent) in enumerate(panels_top):
        col = i % 2
        row = i // 2
        x = col * 580
        y = row * 240
        row_blocks = []
        for j, (k, v) in enumerate(rows):
            ry = j * 26
            row_blocks.append(f"""
            <g transform="translate(0,{ry})">
              <text x="0" y="14" font-size="11" fill="#71717a">{k}</text>
              <text x="540" y="14" text-anchor="end" font-size="11" font-family="{MONO_FAMILY}" fill="#18181b">{v}</text>
            </g>""")
        rows_svg = "".join(row_blocks)
        panel_blocks.append(f"""
        <g transform="translate({x},{y})" filter="url(#cardShadow)">
          <rect width="540" height="220" rx="14" fill="white" stroke="#e4e4e7"/>
          <rect width="540" height="40" rx="14" fill="white"/>
          <rect y="20" width="540" height="20" fill="white"/>
          <line x1="0" y1="40" x2="540" y2="40" stroke="#f4f4f5"/>
          <circle cx="22" cy="20" r="6" fill="{accent}"/>
          <text x="36" y="25" font-size="13" font-weight="700" fill="#18181b">{title}</text>
          <g transform="translate(20,68)">
            {rows_svg}
          </g>
        </g>""")
    panels_svg = "".join(panel_blocks)

    errors = [
        ("16:38:12", "get_messages",      "502", "upstream timeout"),
        ("12:04:09", "send_message",      "429", "rate limit, retry after 12s"),
        ("08:51:42", "download_audio",    "404", "media not found"),
    ]
    error_rows = []
    for i, (ts, where, status, msg) in enumerate(errors):
        y = i * 32
        error_rows.append(f"""
        <g transform="translate(0,{y})">
          <text x="0" y="20" font-family="{MONO_FAMILY}" font-size="11" fill="#a1a1aa">{ts}</text>
          <rect x="80" y="6" width="100" height="20" rx="6" fill="#f4f4f5"/>
          <text x="130" y="20" text-anchor="middle" font-size="11" font-weight="600" fill="#52525b">{where}</text>
          <rect x="200" y="6" width="44" height="20" rx="6" fill="#fee2e2"/>
          <text x="222" y="20" text-anchor="middle" font-size="11" font-weight="700" fill="#b91c1c">{status}</text>
          <text x="264" y="20" font-size="11" fill="#27272a">{msg}</text>
        </g>""")
    error_rows_svg = "".join(error_rows)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" font-family="{FONT_FAMILY}">
  {shell_defs()}
  {app_shell(1440, 900, dark=False, title='Diagnostics', subtitle='Live snapshot of gateway, LLM, database and bot runtime')}

  <g transform="translate(252,96)">
    {panels_svg}
  </g>

  <!-- Recent errors -->
  <g transform="translate(252,592)" filter="url(#cardShadow)">
    <rect width="1140" height="248" rx="14" fill="white" stroke="#e4e4e7"/>
    <g transform="translate(24,28)">
      <text font-size="13" font-weight="700" fill="#18181b">Recent gateway errors</text>
      <text y="18" font-size="11" fill="#71717a">Last 3 non-2xx responses from the WhatsApp gateway.</text>
    </g>
    <g transform="translate(24,80)">
      <text x="0" y="14" font-size="10" font-weight="700" fill="#71717a" letter-spacing="1">TIME</text>
      <text x="80" y="14" font-size="10" font-weight="700" fill="#71717a" letter-spacing="1">ENDPOINT</text>
      <text x="200" y="14" font-size="10" font-weight="700" fill="#71717a" letter-spacing="1">STATUS</text>
      <text x="264" y="14" font-size="10" font-weight="700" fill="#71717a" letter-spacing="1">MESSAGE</text>
      <line x1="0" y1="22" x2="1080" y2="22" stroke="#f4f4f5"/>
      <g transform="translate(0,32)">
        {error_rows_svg}
      </g>
    </g>
  </g>
</svg>
"""


# ---------------------------------------------------------------------------
# Settings page
# ---------------------------------------------------------------------------
def build_settings_page() -> str:
    rows = [
        ("Auth required",       "yes (admin)"),
        ("Environment",         "production"),
        ("Version",             "1.0.0"),
        ("WhatsApp base URL",   "http://wa-gateway:8081"),
        ("Device JID",          "12345...whatsapp.net"),
        ("Text model",          "gpt-4o-mini"),
        ("Vision model",        "gpt-4o-mini"),
        ("Audio model",         "whisper-1"),
        ("Poll interval",       "5 s"),
        ("Database path",       "/data/messages.db"),
    ]
    row_blocks = []
    for i, (k, v) in enumerate(rows):
        y = i * 36
        row_blocks.append(f"""
        <g transform="translate(0,{y})">
          <rect width="700" height="32" rx="8" fill="{'#fafafa' if i%2 else 'white'}"/>
          <text x="14" y="20" font-size="11" fill="#71717a">{k}</text>
          <text x="686" y="20" text-anchor="end" font-size="11" font-family="{MONO_FAMILY}" fill="#18181b">{v}</text>
        </g>""")
    rows_svg = "".join(row_blocks)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" font-family="{FONT_FAMILY}">
  {shell_defs()}
  {app_shell(1440, 900, dark=False, title='Settings', subtitle='Read-only view of the runtime configuration')}

  <g transform="translate(252,96)" filter="url(#cardShadow)">
    <rect width="724" height="500" rx="14" fill="white" stroke="#e4e4e7"/>
    <g transform="translate(24,24)">
      <text font-size="13" font-weight="700" fill="#18181b">Runtime configuration</text>
      <text y="18" font-size="11" fill="#71717a">Edit the .env file (or platform variables) and restart to change.</text>
    </g>
    <g transform="translate(24,68)">
      {rows_svg}
    </g>
  </g>

  <g transform="translate(996,96)" filter="url(#cardShadow)">
    <rect width="396" height="240" rx="14" fill="white" stroke="#e4e4e7"/>
    <g transform="translate(24,24)">
      <text font-size="13" font-weight="700" fill="#18181b">Appearance</text>
      <text y="18" font-size="11" fill="#71717a">Saved in your browser only.</text>
    </g>

    <g transform="translate(24,80)">
      <rect width="348" height="44" rx="10" fill="#f4f4f5"/>
      <g transform="translate(8,8)">
        <rect width="108" height="28" rx="6" fill="white" stroke="#22c55e"/>
        <text x="54" y="18" text-anchor="middle" font-size="11" font-weight="700" fill="#16a34a">{SUN} Light</text>
      </g>
      <g transform="translate(120,8)">
        <rect width="108" height="28" rx="6" fill="#f4f4f5"/>
        <text x="54" y="18" text-anchor="middle" font-size="11" font-weight="600" fill="#52525b">{MOON} Dark</text>
      </g>
      <g transform="translate(232,8)">
        <rect width="108" height="28" rx="6" fill="#f4f4f5"/>
        <text x="54" y="18" text-anchor="middle" font-size="11" font-weight="600" fill="#52525b">System</text>
      </g>
    </g>

    <g transform="translate(24,156)">
      <text font-size="11" fill="#71717a">Theme {RARROW} stored in localStorage as &#8220;whatslang.theme&#8221;.</text>
    </g>
  </g>

  <g transform="translate(996,360)" filter="url(#cardShadow)">
    <rect width="396" height="236" rx="14" fill="white" stroke="#e4e4e7"/>
    <g transform="translate(24,24)">
      <text font-size="13" font-weight="700" fill="#18181b">Account</text>
      <text y="18" font-size="11" fill="#71717a">Single user, configured via env vars.</text>
    </g>
    <g transform="translate(24,76)">
      <text font-size="11" fill="#71717a">Signed in as</text>
      <text x="120" font-size="11" font-weight="700" fill="#18181b">admin</text>
    </g>
    <g transform="translate(24,108)">
      <text font-size="11" fill="#71717a">Session lifetime</text>
      <text x="120" font-size="11" font-weight="700" fill="#18181b">7 days</text>
    </g>
    <g transform="translate(24,140)">
      <text font-size="11" fill="#71717a">Cookie</text>
      <text x="120" font-size="11" font-family="{MONO_FAMILY}" fill="#18181b">whatslang_session</text>
    </g>
    <g transform="translate(24,184)">
      <rect width="120" height="32" rx="8" fill="#fee2e2"/>
      <text x="60" y="20" text-anchor="middle" font-size="11" font-weight="700" fill="#b91c1c">Sign out</text>
    </g>
  </g>
</svg>
"""


# ---------------------------------------------------------------------------
# Login page
# ---------------------------------------------------------------------------
def build_login() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" font-family="{FONT_FAMILY}">
  <defs>
    <linearGradient id="brand" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#22c55e"/>
      <stop offset="100%" stop-color="#16a34a"/>
    </linearGradient>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#fafafa"/>
      <stop offset="50%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#f0fdf4"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#22c55e" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="#22c55e" stop-opacity="0"/>
    </radialGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="20" stdDeviation="30" flood-color="#0f172a" flood-opacity="0.12"/>
    </filter>
  </defs>

  <rect width="1440" height="900" fill="url(#bg)"/>
  <ellipse cx="720" cy="450" rx="600" ry="380" fill="url(#glow)"/>

  <g transform="translate(620,180)">
    <rect width="40" height="40" rx="10" fill="url(#brand)"/>
    <text x="20" y="28" text-anchor="middle" font-size="20" font-weight="700" fill="white">W</text>
    <text x="56" y="28" font-size="20" font-weight="700" fill="#16a34a">Whatslang Console</text>
  </g>

  <g transform="translate(560,260)" filter="url(#shadow)">
    <rect width="320" height="380" rx="22" fill="white" stroke="#e4e4e7"/>
    <g transform="translate(28,32)">
      <text font-size="20" font-weight="700" fill="#18181b">Sign in to continue</text>
      <text y="22" font-size="13" fill="#71717a">Use the credentials configured in your environment.</text>
    </g>

    <g transform="translate(28,108)">
      <text font-size="12" font-weight="600" fill="#18181b">Username</text>
      <rect y="12" width="264" height="40" rx="10" fill="white" stroke="#22c55e"/>
      <text x="14" y="38" font-size="14" fill="#a1a1aa">{KEY}</text>
      <text x="42" y="38" font-size="14" fill="#27272a">admin</text>
    </g>

    <g transform="translate(28,180)">
      <text font-size="12" font-weight="600" fill="#18181b">Password</text>
      <rect y="12" width="264" height="40" rx="10" fill="white" stroke="#e4e4e7"/>
      <text x="14" y="38" font-size="14" fill="#a1a1aa">{LOCK_SOLID}</text>
      <text x="42" y="38" font-size="14" fill="#27272a">{MIDDOT*10}</text>
    </g>

    <g transform="translate(28,260)">
      <rect width="264" height="44" rx="10" fill="url(#brand)"/>
      <text x="132" y="28" text-anchor="middle" font-size="14" font-weight="600" fill="white">Sign in</text>
    </g>

    <text x="160" y="346" text-anchor="middle" font-size="11" fill="#a1a1aa">Single-user {MIDDOT} session cookies signed with HMAC</text>
  </g>

  <text x="720" y="700" text-anchor="middle" font-size="11" fill="#a1a1aa">Whatslang &#183; v1.0</text>
</svg>
"""


# ---------------------------------------------------------------------------
# WhatsApp conversation
# ---------------------------------------------------------------------------
def build_whatsapp_conversation() -> str:
    incoming_color = "#ffffff"
    incoming_text = "#0b141a"
    outgoing_color = "#d9fdd3"
    bubbles = [
        # is_user, text, time, bot_prefix
        (True,  "Hello! How are you?",                          "10:41", None),
        (False, "Olá! Como você está?",                          "10:41", "[ai]"),
        (True,  "Can you tell me a joke?",                       "10:42", None),
        (False, "Why did the developer go broke?\nBecause he used up all his cache.",
                                                                 "10:42", "[joke]"),
        (True,  "[image of food]",                               "12:30", None),
        (False, "Looks like a bowl of poke (about 520 kcal).\nProtein 30g, carbs 60g, fat 18g.\nNice balance! Add a glass of water.",
                                                                 "12:31", "[health]"),
        (True,  "[voice note]",                                  "12:33", None),
        (False, "Transcription:\n\"Bom dia, tudo bem?\"\n\nTranslation:\nGood morning, how are you?",
                                                                 "12:34", "[ai]"),
    ]
    bubble_blocks = []
    y = 80
    for is_user, text, time, prefix in bubbles:
        max_width = 360
        lines = []
        for raw_line in text.split("\n"):
            words = raw_line.split(" ")
            cur = ""
            for w in words:
                test = (cur + " " + w).strip()
                if len(test) > 42:
                    lines.append(cur)
                    cur = w
                else:
                    cur = test
            lines.append(cur)
        height = 26 + 16 * len(lines) + (16 if prefix else 0)
        x = 540 - max_width if not is_user else 800 - max_width
        if is_user:
            x = 800 - max_width
        else:
            x = 60
        fill = outgoing_color if is_user else incoming_color
        text_color = incoming_text
        prefix_svg = ""
        if prefix:
            prefix_svg = f'<text x="14" y="20" font-size="10" font-weight="700" fill="#16a34a" font-family="{MONO_FAMILY}">{prefix}</text>'
        line_svgs = []
        for i, l in enumerate(lines):
            ly = (40 if prefix else 24) + i * 16
            line_svgs.append(f'<text x="14" y="{ly}" font-size="13" fill="{text_color}">{l}</text>')
        lines_svg = "\n        ".join(line_svgs)

        bubble_blocks.append(f"""
        <g transform="translate({x},{y})">
          <rect width="{max_width}" height="{height}" rx="12" fill="{fill}" stroke="#e4e4e7"/>
          {prefix_svg}
          {lines_svg}
          <text x="{max_width-12}" y="{height-8}" text-anchor="end" font-size="10" fill="#667781">{time}</text>
        </g>""")
        y += height + 12
    bubbles_svg = "".join(bubble_blocks)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 1100" font-family="{FONT_FAMILY}">
  <defs>
    <linearGradient id="wabg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#efeae2"/>
      <stop offset="100%" stop-color="#ddd5c8"/>
    </linearGradient>
    <pattern id="dots" patternUnits="userSpaceOnUse" width="20" height="20">
      <circle cx="2" cy="2" r="1" fill="#cdc6b6" opacity="0.35"/>
    </pattern>
  </defs>

  <rect width="880" height="1100" fill="url(#wabg)"/>
  <rect width="880" height="1100" fill="url(#dots)"/>

  <!-- Header bar -->
  <g>
    <rect width="880" height="64" fill="#005c4b"/>
    <circle cx="42" cy="32" r="20" fill="#dcfce7"/>
    <text x="42" y="38" text-anchor="middle" font-size="16" font-weight="700" fill="#166534">F</text>
    <text x="76" y="28" font-size="14" font-weight="700" fill="white">Friends</text>
    <text x="76" y="48" font-size="11" fill="#bbf7d0">online &#183; bots: ai, joke, health</text>
  </g>

  <!-- Bubbles -->
  <g>
    {bubbles_svg}
  </g>

  <!-- Composer -->
  <g transform="translate(0,1040)">
    <rect width="880" height="60" fill="#f0f2f5"/>
    <rect x="60" y="14" width="700" height="32" rx="16" fill="white"/>
    <text x="80" y="34" font-size="13" fill="#667781">Type a message{ELLIPSIS}</text>
    <circle cx="800" cy="30" r="20" fill="#005c4b"/>
    <text x="800" y="36" text-anchor="middle" font-size="14" fill="white">{RARROW}</text>
  </g>
</svg>
"""


# ---------------------------------------------------------------------------
# Architecture diagram
# ---------------------------------------------------------------------------
def build_architecture() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" font-family="{FONT_FAMILY}">
  <defs>
    <linearGradient id="card" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#fafafa"/>
    </linearGradient>
    <filter id="cardShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="10" flood-color="#0f172a" flood-opacity="0.10"/>
    </filter>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,6 L9,3 z" fill="#16a34a"/>
    </marker>
    <marker id="arrowDim" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,6 L9,3 z" fill="#94a3b8"/>
    </marker>
  </defs>

  <rect width="1280" height="720" fill="#f8fafc"/>

  <text x="640" y="48" text-anchor="middle" font-size="22" font-weight="700" fill="#0f172a">Whatslang architecture</text>
  <text x="640" y="72" text-anchor="middle" font-size="13" fill="#475569">A single FastAPI process serves the SPA, talks to a WhatsApp gateway, and runs a thread per (bot, chat).</text>

  <!-- WA users -->
  <g transform="translate(40,140)" filter="url(#cardShadow)">
    <rect width="200" height="100" rx="14" fill="url(#card)" stroke="#e2e8f0"/>
    <text x="100" y="34" text-anchor="middle" font-size="13" font-weight="600" fill="#0f172a">{PHONE} WhatsApp users</text>
    <text x="100" y="56" text-anchor="middle" font-size="11" fill="#64748b">Friends &#183; groups &#183; DMs</text>
    <text x="100" y="74" text-anchor="middle" font-size="11" fill="#64748b">Text &#183; image &#183; audio &#183; video</text>
  </g>

  <!-- WA gateway -->
  <g transform="translate(40,340)" filter="url(#cardShadow)">
    <rect width="200" height="120" rx="14" fill="url(#card)" stroke="#e2e8f0"/>
    <rect x="20" y="16" width="36" height="36" rx="8" fill="#dcfce7"/>
    <text x="38" y="40" text-anchor="middle" font-size="16">{SAT}</text>
    <text x="64" y="34" font-size="13" font-weight="600" fill="#0f172a">WhatsApp gateway</text>
    <text x="64" y="50" font-size="10" fill="#64748b">whatsapp-mcp / wha-mcp</text>
    <text x="20" y="78" font-size="11" fill="#475569">REST: list chats, list</text>
    <text x="20" y="94" font-size="11" fill="#475569">messages, send, download</text>
    <text x="20" y="110" font-size="11" fill="#475569">media, presence.</text>
  </g>

  <!-- Backend center -->
  <g transform="translate(330,140)" filter="url(#cardShadow)">
    <rect width="620" height="440" rx="18" fill="white" stroke="#e2e8f0"/>
    <rect width="620" height="44" rx="18" fill="#052e16"/>
    <rect y="22" width="620" height="22" fill="#052e16"/>
    <text x="20" y="29" font-size="14" font-weight="700" fill="#86efac">Whatslang backend &#183; FastAPI</text>
    <text x="600" y="29" text-anchor="end" font-size="10" fill="#bbf7d0">app/ &#183; Python 3.10+</text>

    <g transform="translate(20,68)">
      <g>
        <rect width="280" height="84" rx="10" fill="#f0fdf4" stroke="#bbf7d0"/>
        <text x="14" y="22" font-size="12" font-weight="700" fill="#166534">HTTP layer &#183; routers/</text>
        <g font-size="11" fill="#15803d">
          <text x="14" y="40">/api/auth &#183; /api/chats &#183; /api/bots</text>
          <text x="14" y="56">/api/system &#183; /api/diagnostics</text>
          <text x="14" y="72">SPA mount &#183; /health &#183; /ready</text>
        </g>
      </g>

      <g transform="translate(300,0)">
        <rect width="280" height="84" rx="10" fill="#eff6ff" stroke="#bfdbfe"/>
        <text x="14" y="22" font-size="12" font-weight="700" fill="#1d4ed8">Bot manager &#183; services/</text>
        <g font-size="11" fill="#1e40af">
          <text x="14" y="40">Per (bot, chat) thread</text>
          <text x="14" y="56">Ring-buffer logs &#183; live status</text>
          <text x="14" y="72">Resume from DB on boot</text>
        </g>
      </g>

      <g transform="translate(0,100)">
        <rect width="280" height="84" rx="10" fill="#f5f3ff" stroke="#ddd6fe"/>
        <text x="14" y="22" font-size="12" font-weight="700" fill="#6d28d9">Bot runner &#183; bots/base.py</text>
        <g font-size="11" fill="#5b21b6">
          <text x="14" y="40">Polls gateway &#183; dedup &#183; gates</text>
          <text x="14" y="56">Splits long replies &#183; logs</text>
          <text x="14" y="72">Per-chat settings (context, ...)</text>
        </g>
      </g>

      <g transform="translate(300,100)">
        <rect width="280" height="84" rx="10" fill="#fffbeb" stroke="#fde68a"/>
        <text x="14" y="22" font-size="12" font-weight="700" fill="#92400e">LLM service &#183; services/llm.py</text>
        <g font-size="11" fill="#78350f">
          <text x="14" y="40">OpenAI / LiteLLM client</text>
          <text x="14" y="56">Text &#183; vision &#183; Whisper</text>
          <text x="14" y="72">ffmpeg: video {RARROW} audio</text>
        </g>
      </g>

      <g transform="translate(0,200)">
        <rect width="280" height="84" rx="10" fill="#fdf4ff" stroke="#f5d0fe"/>
        <text x="14" y="22" font-size="12" font-weight="700" fill="#a21caf">SQLite repository &#183; db.py</text>
        <g font-size="11" fill="#86198f">
          <text x="14" y="40">chats &#183; bot_chat_assignments</text>
          <text x="14" y="56">processed_messages (dedup)</text>
          <text x="14" y="72">Single-file, on a volume</text>
        </g>
      </g>

      <g transform="translate(300,200)">
        <rect width="280" height="84" rx="10" fill="#fef2f2" stroke="#fecaca"/>
        <text x="14" y="22" font-size="12" font-weight="700" fill="#b91c1c">Auth &#183; auth.py</text>
        <g font-size="11" fill="#991b1b">
          <text x="14" y="40">Single user from env</text>
          <text x="14" y="56">HMAC-signed cookies</text>
          <text x="14" y="72">Optional (toggle off w/ blanks)</text>
        </g>
      </g>

      <g transform="translate(0,300)">
        <rect width="580" height="60" rx="10" fill="#0f172a"/>
        <text x="14" y="24" font-size="12" font-weight="700" fill="#bbf7d0">Bot catalog &#183; bots/__init__.py &#183; declarative BotSpec(...) registry</text>
        <text x="14" y="44" font-size="11" font-family="{MONO_FAMILY}" fill="#86efac">{GLOBE} translation   &#183;   {FLAG_BR} trilingual_en_pt_el   &#183;   {LAUGH} joke   &#183;   {SALAD} health_coach   &#183;   {PLUS_HEAVY} your bot here</text>
      </g>
    </g>
  </g>

  <!-- Browser -->
  <g transform="translate(1040,140)" filter="url(#cardShadow)">
    <rect width="200" height="100" rx="14" fill="url(#card)" stroke="#e2e8f0"/>
    <text x="100" y="34" text-anchor="middle" font-size="13" font-weight="600" fill="#0f172a">{CHART} React console</text>
    <text x="100" y="56" text-anchor="middle" font-size="11" fill="#64748b">Vite + Tailwind v4</text>
    <text x="100" y="74" text-anchor="middle" font-size="11" fill="#64748b">React Router &#183; TanStack</text>
  </g>

  <!-- LLM provider -->
  <g transform="translate(1040,340)" filter="url(#cardShadow)">
    <rect width="200" height="120" rx="14" fill="url(#card)" stroke="#e2e8f0"/>
    <rect x="20" y="16" width="36" height="36" rx="8" fill="#fffbeb"/>
    <text x="38" y="40" text-anchor="middle" font-size="16">{ROBOT}</text>
    <text x="64" y="34" font-size="13" font-weight="600" fill="#0f172a">LLM provider</text>
    <text x="64" y="50" font-size="10" fill="#64748b">OpenAI &#183; LiteLLM &#183; Azure</text>
    <text x="20" y="78" font-size="11" fill="#475569">Chat completions &#183; vision</text>
    <text x="20" y="94" font-size="11" fill="#475569">Whisper transcription</text>
    <text x="20" y="110" font-size="11" fill="#475569">Pluggable base URL</text>
  </g>

  <!-- Volume -->
  <g transform="translate(560,624)" filter="url(#cardShadow)">
    <rect width="160" height="56" rx="10" fill="url(#card)" stroke="#e2e8f0"/>
    <text x="80" y="22" text-anchor="middle" font-size="12" font-weight="600" fill="#0f172a">{DATABASE}  /data volume</text>
    <text x="80" y="42" text-anchor="middle" font-size="10" fill="#64748b">messages.db (SQLite)</text>
  </g>

  <!-- Arrows -->
  <line x1="140" y1="240" x2="140" y2="334" stroke="#94a3b8" stroke-width="2" stroke-dasharray="4 4" marker-end="url(#arrowDim)"/>
  <text x="148" y="290" font-size="10" fill="#64748b">WhatsApp protocol</text>

  <line x1="330" y1="400" x2="246" y2="400" stroke="#16a34a" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="252" y="392" font-size="10" fill="#16a34a">poll &#183; send &#183; download</text>

  <line x1="950" y1="190" x2="1034" y2="190" stroke="#16a34a" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="970" y="180" font-size="10" fill="#16a34a">/api/* &#183; SPA</text>

  <line x1="950" y1="400" x2="1034" y2="400" stroke="#16a34a" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="960" y="392" font-size="10" fill="#16a34a">REST</text>

  <line x1="640" y1="580" x2="640" y2="618" stroke="#16a34a" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="648" y="606" font-size="10" fill="#16a34a">read/write</text>
</svg>
"""


# ---------------------------------------------------------------------------
# Bot lifecycle
# ---------------------------------------------------------------------------
def build_bot_lifecycle() -> str:
    cards = [
        ("Poll gateway",
         ["Every poll_interval_seconds",
          "the runner asks the gateway",
          "for new messages on its",
          "assigned chat.",
          "",
          "Skips if the manager has",
          "paused this bot."]),
        ("Filter &amp; gate",
         ["Drop self-messages unless",
          "self-answer is on. Drop",
          "already-processed IDs",
          "(per bot, per chat).",
          "",
          "Honors prefix matching",
          "when bot.prefix is set."]),
        ("Resolve media",
         ["Download attachment via",
          "the gateway. For audio:",
          "Whisper. For video: extract",
          "audio with ffmpeg, then",
          "transcribe.",
          "Images go straight to the",
          "vision-capable LLM call."]),
        ("Call LLM",
         ["Build messages from BotSpec:",
          "system prompt + last N turns",
          "+ this user message + media.",
          "Call OpenAI/LiteLLM client.",
          "",
          "N = context_size from the",
          "per-chat assignment."]),
        ("Send reply",
         ["Optional bot prefix is added",
          "(e.g. \"[ai] ...\").",
          "Long replies are split into",
          "~3500-char chunks.",
          "",
          "Can redirect to another",
          "chat (forward_to_chat_id)."]),
    ]
    blocks = []
    for i, (title, lines) in enumerate(cards):
        x = 40 + i * 224
        text_lines = []
        for j, l in enumerate(lines):
            ly = j * 18
            color = "#475569" if l else "#475569"
            text_lines.append(f'<text y="{ly}" font-size="11" fill="{color}">{l}</text>')
        text_svg = "\n        ".join(text_lines)
        blocks.append(f"""
    <g transform="translate({x},140)" filter="url(#cardShadow)">
      <rect width="200" height="220" rx="14" fill="url(#card)" stroke="#e2e8f0"/>
      <circle cx="32" cy="36" r="16" fill="#16a34a"/>
      <text x="32" y="41" text-anchor="middle" font-size="13" font-weight="700" fill="white">{i+1}</text>
      <text x="60" y="42" font-size="13" font-weight="700" fill="#0f172a">{title}</text>
      <g transform="translate(20,72)">
        {text_svg}
      </g>
    </g>""")
    cards_svg = "".join(blocks)

    arrows = []
    for i in range(4):
        x1 = 240 + i * 224
        x2 = x1 + 22
        arrows.append(f'<line x1="{x1}" y1="250" x2="{x2}" y2="250" marker-end="url(#arrow)"/>')
    arrows_svg = "".join(arrows)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 480" font-family="{FONT_FAMILY}">
  <defs>
    <linearGradient id="card" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#fafafa"/>
    </linearGradient>
    <filter id="cardShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="10" flood-color="#0f172a" flood-opacity="0.10"/>
    </filter>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,6 L9,3 z" fill="#16a34a"/>
    </marker>
  </defs>

  <rect width="1280" height="480" fill="#f8fafc"/>

  <text x="640" y="48" text-anchor="middle" font-size="22" font-weight="700" fill="#0f172a">Per-message bot lifecycle</text>
  <text x="640" y="72" text-anchor="middle" font-size="13" fill="#475569">Each message goes through a fixed pipeline. The runner is the same for every bot {EMDASH} only the BotSpec changes.</text>

  {cards_svg}

  <g stroke="#16a34a" stroke-width="2">
    {arrows_svg}
  </g>

  <text x="640" y="412" text-anchor="middle" font-size="11" fill="#64748b">All steps are observable in /api/diagnostics and the per-bot log modal.</text>
</svg>
"""


# ---------------------------------------------------------------------------
# Build everything
# ---------------------------------------------------------------------------
def main() -> None:
    files = {
        "hero.svg":                    build_hero(),
        "dashboard-light.svg":         _dashboard(dark=False),
        "dashboard-dark.svg":          _dashboard(dark=True),
        "chats.svg":                   build_chats(),
        "chat-detail.svg":             build_chat_detail(),
        "bots.svg":                    build_bots_page(),
        "bot-settings-modal.svg":      build_bot_settings_modal(),
        "bot-logs-modal.svg":          build_bot_logs_modal(),
        "diagnostics.svg":             build_diagnostics(),
        "settings.svg":                build_settings_page(),
        "login.svg":                   build_login(),
        "whatsapp-conversation.svg":   build_whatsapp_conversation(),
        "architecture.svg":            build_architecture(),
        "bot-lifecycle.svg":           build_bot_lifecycle(),
    }
    for name, content in files.items():
        path = write_svg(name, content)
        print(f"wrote {path.relative_to(path.parent.parent.parent)} ({path.stat().st_size} bytes)")
    print(f"\n{len(files)} SVGs written and validated.")


if __name__ == "__main__":
    main()
