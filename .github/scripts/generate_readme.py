#!/usr/bin/env python3
import json
import os
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

USERNAME = "OPX-Aminul"
ROOT = Path(__file__).resolve().parents[2]


def github_api(path):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    url = f"https://api.github.com{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "opx-aminul-profile-readme",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)

    result = subprocess.run(
        ["gh", "api", path],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


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
    return quote(str(text).replace("-", "--").replace("_", "__"), safe="")


user = github_api(f"/users/{USERNAME}")
followers = int(user.get("followers") or 0)
following = int(user.get("following") or 0)
public_repos = int(user.get("public_repos") or 0)
bio = md_escape(user.get("bio") or "OPX developer")

repos = paginate(f"/users/{USERNAME}/repos?type=owner&sort=updated")
public = [r for r in repos if not r.get("private")]
own = [r for r in public if r.get("name") != USERNAME and not r.get("fork")]
forks = [r for r in public if r.get("name") != USERNAME and r.get("fork")]
stars = sum(int(r.get("stargazers_count") or 0) for r in public)
fork_count = sum(int(r.get("forks_count") or 0) for r in public)

flagship = next((r for r in own if r.get("name") == "OPXoneshot"), own[0] if own else None)
more = [r for r in own if flagship is None or r["name"] != flagship["name"]]

synced = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
views = (
    f"https://komarev.com/ghpvc/?username={USERNAME}"
    "&style=for-the-badge&color=00e5ff&label=PROFILE+VIEWS"
)
followers_badge = (
    f"https://img.shields.io/badge/FOLLOWERS-{followers}-7c4dff"
    "?style=for-the-badge&logo=github&logoColor=white"
)
stars_badge = (
    f"https://img.shields.io/badge/STARS-{stars}-00ffa3"
    "?style=for-the-badge&logo=github&logoColor=white"
)
repos_badge = (
    f"https://img.shields.io/badge/PUBLIC%20REPOS-{public_repos}-7c4dff"
    "?style=for-the-badge&logo=github&logoColor=white"
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

asset = f"https://raw.githubusercontent.com/{USERNAME}/{USERNAME}/main/assets"

own_rows = []
for r in own:
    lang = r.get("primaryLanguage")
    if isinstance(lang, dict):
        lang_name = lang.get("name") or "-"
    else:
        lang_name = r.get("language") or "-"
    desc = md_escape(r.get("description")) or "No description"
    own_rows.append(
        f"| [{r['name']}]({r['html_url']}) | {desc} | {lang_name} | {int(r.get('stargazers_count') or 0)} |"
    )

fork_rows = []
for r in forks:
    lang_name = r.get("language") or "-"
    desc = md_escape(r.get("description")) or "No description"
    fork_rows.append(
        f"| [{r['name']}]({r['html_url']}) | {desc} | {lang_name} |"
    )

more_badges = []
for r in more:
    desc = (r.get("description") or r["name"]).split(".")[0][:42]
    more_badges.append(
        f'  <a href="{r["html_url"]}">'
        f'<img src="https://img.shields.io/badge/{shield_label(r["name"])}-{shield_label(desc)}-7c4dff'
        f'?style=for-the-badge&logo=github&logoColor=white" alt="{r["name"]}"/></a>'
    )

flagship_block = ""
if flagship:
    pin = (
        f"https://github-readme-stats.vercel.app/api/pin/?username={USERNAME}"
        f"&repo={flagship['name']}&theme=tokyonight&hide_border=true"
    )
    flagship_block = f"""## Flagship Project

Live pin for **[{flagship['name']}]({flagship['html_url']})** — only rendered because this public repo exists right now.

<p align="center">
  <a href="{flagship['html_url']}">
    <img src="{pin}" width="90%" alt="{flagship['name']}"/>
  </a>
</p>
"""
    if more_badges:
        flagship_block += """
### More from me

<p align="center">
""" + "\n".join(more_badges) + """
</p>
"""

own_table = "\n".join(own_rows) if own_rows else "| _No public original repositories right now_ | | | |"
fork_section = ""
if fork_rows:
    fork_section = f"""
## Public forks

These appear only while the fork still exists and is public.

| Repository | Description | Language |
| --- | --- | --- |
{chr(10).join(fork_rows)}
"""

readme = f"""<!-- Generated live from GitHub API. Do not edit by hand. -->

<p align="center">
  <img src="{asset}/banner.svg" width="100%" alt="OPX-Aminul banner"/>
</p>

<p align="center">
  <a href="https://github.com/{USERNAME}"><img src="{views}" alt="Profile views"/></a>
  <a href="https://github.com/{USERNAME}?tab=followers"><img src="{followers_badge}" alt="Followers"/></a>
  <a href="https://github.com/{USERNAME}?tab=repositories"><img src="{stars_badge}" alt="Stars"/></a>
  <a href="https://github.com/{USERNAME}?tab=repositories"><img src="{repos_badge}" alt="Public repos"/></a>
</p>

<p align="center">
  <img src="{asset}/divider.svg" width="100%" alt="divider"/>
</p>

---

## About Me

<p align="center">
  <img src="{asset}/terminal.svg" width="100%" alt="whoami terminal"/>
</p>

<p align="center">
  <img src="{asset}/ticker.svg" width="100%" alt="skills ticker"/>
</p>

- **{bio}**
- **Security Researcher** — WiFi/WPS internals, then defense
- **AI Engineer** — models that learn from real attempts
- **Android Developer** — tools that run in your pocket
- **Self-taught** — curiosity and a terminal

Live snapshot: **{followers}** followers, **{following}** following, **{public_repos}** public repos, **{stars}** stars, **{fork_count}** forks. Synced `{synced}`.

---

## Tech I Love

<p align="center">
  <img src="https://skillicons.dev/icons?i=python,java,javascript,typescript,react,nodejs,flask,git,github,docker,linux,bash&perline=12" alt="Core skills"/><br/><br/>
  <img src="https://skillicons.dev/icons?i=postgres,mysql,sqlite,redis,tensorflow,pytorch,kali,androidstudio,vscode,raspberrypi,supabase,githubactions&perline=12" alt="Tools and platforms"/>
</p>

---

## Live GitHub Stats

<p align="center">
  <img src="{stats}" width="100%" alt="GitHub stats"/><br/>
  <img src="{streak}" width="100%" alt="GitHub streak"/><br/>
  <img src="{langs}" width="100%" alt="Top languages"/><br/>
  <img src="{graph}" width="100%" alt="Activity graph"/>
</p>

---

## Achievements

<p align="center">
  <img src="{summary}" width="100%" alt="Profile summary"/><br/>
  <img src="{commit_lang}" width="49%" alt="Commit languages"/>
  <img src="{repos_lang}" width="49%" alt="Repos per language"/>
</p>

---

{flagship_block}

## Public repositories

This table is built from the GitHub API. Missing or private repos are omitted automatically.

| Repository | Description | Language | Stars |
| --- | --- | --- | --- |
{own_table}
{fork_section}

---

## Find Me

<p align="center">
  <a href="https://github.com/{USERNAME}"><img src="https://img.shields.io/badge/OPX--Aminul-GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"/></a>
  <a href="https://github.com/{USERNAME}?tab=repositories"><img src="https://img.shields.io/badge/All-Repositories-7c4dff?style=for-the-badge&logo=git&logoColor=white" alt="Repos"/></a>
  <a href="https://github.com/{USERNAME}?tab=followers"><img src="https://img.shields.io/badge/Followers-{followers}-00e5ff?style=for-the-badge&logo=github" alt="Followers"/></a>
</p>

<p align="center">
  <img src="{asset}/footer.svg" width="100%" alt="footer"/>
</p>
"""

(ROOT / "README.md").write_text(readme, encoding="utf-8")
print(f"Wrote README.md followers={followers} public_repos={public_repos} own={len(own)} forks={len(forks)}")
