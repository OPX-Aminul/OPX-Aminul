#!/usr/bin/env python3
import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = "OPX-Aminul"
WEBSITE = "https://opaminulff.vercel.app/"
ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"

FEATURED = [
    "OPXoneshot",
    "OPX-wifi4",
    "OPX-Demon-ok",
    "nethunter-all-kernel",
]

ACH_COLORS = {
    "Quickdraw": "00e5ff",
    "YOLO": "ff5470",
    "Galaxy Brain": "7c4dff",
    "Pull Shark": "00ffa3",
    "Pair Extraordinaire": "f9a825",
    "Starstruck": "ffb300",
    "Arctic Code Vault Contributor": "8bc34a",
    "Public Sponsor": "ea4aaa",
}

PULL_SHARK_TIERS = [(2, "base"), (16, "bronze"), (128, "silver"), (1024, "gold")]
STARSTRUCK_TIERS = [(16, "base")]


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

    try:
        result = subprocess.run(
            ["gh", "api", path],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except (FileNotFoundError, OSError):
        pass  # no gh CLI here: fall through to the plain public API

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


def shield_label(text):
    """shields.io static badge escaping: _ is space, - is --, _ is __"""
    return text.replace("_", "__").replace("-", "--").replace(" ", "_")


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


def unlocked_achievements():
    """Read the badges GitHub already granted from the public achievements tab."""
    try:
        req = urllib.request.Request(
            f"https://github.com/{USERNAME}?tab=achievements",
            headers={"User-Agent": "Mozilla/5.0 (compatible; profile-readme)"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", "ignore")
    except Exception:
        return []
    names = []
    for name in re.findall(r'alt="Achievement: ([^"]+)"', html):
        if name not in names:
            names.append(name)
    return names


def merged_pr_total():
    try:
        data = github_api(
            f"/search/issues?q=is%3Apr+is%3Amerged+author%3A{USERNAME}", authed=False
        )
        return int(data.get("total_count") or 0)
    except Exception:
        return 0


def next_tier(value, tiers):
    for mark, name in tiers:
        if value < mark:
            return mark, name
    return tiers[-1][0], tiers[-1][1]


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

merged_prs = merged_pr_total()
shark_mark, shark_tier = next_tier(merged_prs, PULL_SHARK_TIERS)
star_mark, star_tier = next_tier(stars, STARSTRUCK_TIERS)

unlocked = unlocked_achievements()
badge_row = []
for name in unlocked:
    color = ACH_COLORS.get(name, "00e5ff")
    badge_row.append(
        f'  <a href="https://github.com/{USERNAME}?tab=achievements">'
        f'<img src="https://img.shields.io/badge/{shield_label(name)}-unlocked-{color}'
        f'?style=for-the-badge&logo=github&logoColor=white" alt="{name}"/></a>'
    )

progress_row = [
    f'  <img src="https://img.shields.io/badge/{shield_label("Pull Shark")}-'
    f'{merged_prs}_merged_PR-00ffa3?style=for-the-badge&logo=git&logoColor=white" '
    f'alt="Pull Shark: {merged_prs} merged pull requests"/>',
    f'  <img src="https://img.shields.io/badge/{shield_label("Starstruck")}-'
    f'{stars}_of_{star_mark}_stars-ffb300?style=for-the-badge&logo=github&logoColor=white" '
    f'alt="Starstruck: {stars} of {star_mark} stars"/>',
]

achievements_block = f"""## Achievements

<p align="center">
{chr(10).join(badge_row) if badge_row else '  <em>Badges are syncing — check back soon.</em>'}
</p>

<p align="center">
{chr(10).join(progress_row)}
</p>

<p align="center"><sub>Read live from GitHub's achievements tab · next Pull Shark tier ({shark_tier}) at {shark_mark} merged PRs · next Starstruck tier ({star_tier}) at {star_mark} stars</sub></p>"""

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

{achievements_block}

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
    f"Wrote README.md followers={followers} stars={stars} merged_prs={merged_prs} "
    f"achievements={unlocked} featured={[r['name'] for r in featured]}"
)
