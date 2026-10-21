#!/usr/bin/env python3
import json
import os
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = "OPX-Aminul"
WEBSITE = "https://opaminulff.vercel.app/"
ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"

FEATURED = [
    "OPX-Demon",
    "OPXoneshot",
    "OPX-wifi4",
    "nethunter-all-kernel",
]


def github_api(path, authed=True):
    url = f"https://api.github.com{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "opx-aminul-profile-readme",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if authed and token:
        headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)

    result = subprocess.run(
        ["gh", "api", path],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return json.loads(result.stdout)

    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "opx-aminul-profile-readme",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def paginate(path):
    items = []
    page = 1
    while True:
        sep = "&" if "?" in path else "?"
        chunk = github_api(f"{path}{sep}per_page=100&page={page}")
        if not chunk:
            break
        items.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return items


def md_escape(text):
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def badge_svg(label, value, color):
    label = str(label).upper()
    value = str(value)
    char_w = 7.5
    left = max(86, 28 + char_w * len(label))
    right = max(32, 20 + char_w * len(value))
    width = left + right
    lx = left / 2
    rx = left + right / 2
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width:.1f}" height="28" role="img" aria-label="{escape(label)}: {escape(value)}">
  <title>{escape(label)}: {escape(value)}</title>
  <g shape-rendering="crispEdges">
    <rect width="{left:.1f}" height="28" fill="#555"/>
    <rect x="{left:.1f}" width="{right:.1f}" height="28" fill="{color}"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="{lx:.1f}" y="18">{escape(label)}</text>
    <text x="{rx:.1f}" y="18" font-weight="bold">{escape(value)}</text>
  </g>
</svg>
'''


user = github_api(f"/users/{USERNAME}", authed=False)
followers = int(user.get("followers") or 0)
following = int(user.get("following") or 0)

repos = paginate(f"/users/{USERNAME}/repos?type=owner&sort=updated")
public = [r for r in repos if not r.get("private") and r.get("name") != USERNAME]
own = [r for r in public if not r.get("fork")]
stars = sum(int(r.get("stargazers_count") or 0) for r in public)
by_name = {r["name"]: r for r in own}

featured = [by_name[n] for n in FEATURED if n in by_name]
if len(featured) < 4:
    extra = sorted(
        [r for r in own if r["name"] not in FEATURED],
        key=lambda r: (
            int(r.get("stargazers_count") or 0),
            r.get("updated_at") or "",
        ),
        reverse=True,
    )
    featured.extend(extra[: max(0, 4 - len(featured))])

ASSETS.mkdir(parents=True, exist_ok=True)
(ASSETS / "followers.svg").write_text(badge_svg("FOLLOWERS", followers, "#7c4dff"), encoding="utf-8")
(ASSETS / "stars.svg").write_text(badge_svg("STARS", stars, "#00ffa3"), encoding="utf-8")

synced = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
cache = int(time.time())
asset = f"https://raw.githubusercontent.com/{USERNAME}/{USERNAME}/main/assets"
views = (
    f"https://komarev.com/ghpvc/?username={USERNAME}"
    "&style=for-the-badge&color=00e5ff&label=PROFILE+VIEWS"
)
stats = (
    f"https://github-readme-stats.vercel.app/api?username={USERNAME}"
    "&show_icons=true&theme=tokyonight&hide_border=true&count_private=true"
)
streak = (
    f"https://streak-stats.demolab.com/?user={USERNAME}"
    "&theme=tokyonight&hide_border=true&ring=00e5ff&fire=ff5470&currStreakLabel=7c4dff"
)
langs = (
    f"https://github-readme-stats.vercel.app/api/top-langs/?username={USERNAME}"
    "&layout=compact&theme=tokyonight&hide_border=true&langs_count=8"
)
graph = (
    f"https://github-readme-activity-graph.vercel.app/graph?username={USERNAME}"
    "&theme=tokyo-night&hide_border=true&area=true&color=00e5ff&line=7c4dff&point=ff5470"
)
summary = (
    f"https://github-profile-summary-cards.vercel.app/api/cards/profile-details"
    f"?username={USERNAME}&theme=tokyonight"
)
commit_lang = (
    f"https://github-profile-summary-cards.vercel.app/api/cards/most-commit-language"
    f"?username={USERNAME}&theme=tokyonight"
)
repos_lang = (
    f"https://github-profile-summary-cards.vercel.app/api/cards/repos-per-language"
    f"?username={USERNAME}&theme=tokyonight"
)

featured_pins = []
for r in featured:
    pin = (
        f"https://github-readme-stats.vercel.app/api/pin/?username={USERNAME}"
        f"&repo={r['name']}&theme=tokyonight&hide_border=true"
    )
    featured_pins.append(
        f'  <a href="{r["html_url"]}"><img src="{pin}" height="140" alt="{r["name"]}"/></a>'
    )

featured_block = ""
if featured_pins:
    featured_block = """## Featured work

<p align="center">
""" + "\n".join(featured_pins) + """
</p>
"""

readme = f"""<!-- Generated live from GitHub API. Do not edit by hand. -->

<p align="center">
  <img src="{asset}/banner.svg?v={cache}" width="100%" alt="OPX-Aminul banner"/>
</p>

<p align="center">
  <a href="https://github.com/{USERNAME}"><img src="{views}" alt="Profile views"/></a>
  <a href="https://github.com/{USERNAME}?tab=followers"><img src="{asset}/followers.svg?v={cache}" alt="Followers"/></a>
  <a href="https://github.com/{USERNAME}?tab=repositories"><img src="{asset}/stars.svg?v={cache}" alt="Stars"/></a>
  <a href="{WEBSITE}"><img src="https://img.shields.io/badge/Website-opaminulff-00e5ff?style=for-the-badge" alt="Website"/></a>
</p>

<p align="center">
  <img src="{asset}/divider.svg?v={cache}" width="100%" alt="divider"/>
</p>

---

## About

<p align="center">
  <img src="{asset}/terminal.svg?v={cache}" width="100%" alt="whoami terminal"/>
</p>

<p align="center">
  <img src="{asset}/ticker.svg?v={cache}" width="100%" alt="skills ticker"/>
</p>

I build mobile and wireless security tools — from Android pentest suites to WPS research frameworks.

- **Android security** — chroot/QEMU engines, USB Wi-Fi, HID, and on-device tooling
- **Wireless research** — WPS internals, Pixie Dust, monitor-mode labs
- **Open source** — ship usable tools, not just writeups
- **Location** — Bangladesh · currently building [OPX-Demon](https://github.com/{USERNAME}/OPX-Demon)

Live snapshot: **{followers}** followers · **{following}** following · **{stars}** stars · synced `{synced}`

---

## Stack

<p align="center">
  <img src="https://skillicons.dev/icons?i=python,java,kotlin,javascript,typescript,linux,bash,git,github,docker,androidstudio,vscode&perline=12" alt="Core skills"/><br/><br/>
  <img src="https://skillicons.dev/icons?i=react,nodejs,flask,postgres,mysql,sqlite,redis,kali,raspberrypi,supabase,githubactions,nginx&perline=12" alt="Tools and platforms"/>
</p>

---

## GitHub

<p align="center">
  <img src="{stats}" width="100%" alt="GitHub stats"/><br/>
  <img src="{streak}" width="100%" alt="GitHub streak"/><br/>
  <img src="{langs}" width="100%" alt="Top languages"/><br/>
  <img src="{graph}" width="100%" alt="Activity graph"/>
</p>

---

## Activity

<p align="center">
  <img src="{summary}" width="100%" alt="Profile summary"/><br/>
  <img src="{commit_lang}" width="49%" alt="Commit languages"/>
  <img src="{repos_lang}" width="49%" alt="Repos per language"/>
</p>

---

{featured_block}

---

## Links

<p align="center">
  <a href="https://github.com/{USERNAME}"><img src="https://img.shields.io/badge/OPX--Aminul-GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"/></a>
  <a href="{WEBSITE}"><img src="https://img.shields.io/badge/Website-opaminulff-00e5ff?style=for-the-badge" alt="Website"/></a>
  <a href="https://github.com/{USERNAME}?tab=repositories"><img src="https://img.shields.io/badge/All-Repositories-7c4dff?style=for-the-badge&logo=git&logoColor=white" alt="Repos"/></a>
</p>

<p align="center">
  <img src="{asset}/footer.svg?v={cache}" width="100%" alt="footer"/>
</p>
"""

(ROOT / "README.md").write_text(readme, encoding="utf-8")
print(
    f"Wrote README.md followers={followers} stars={stars} featured={[r['name'] for r in featured]}"
)
