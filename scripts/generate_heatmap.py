#!/usr/bin/env python3
import json
import os
from datetime import datetime
import urllib.request

USERNAME = os.environ.get("USERNAME", "Ayinkx01")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            level
          }
        }
      }
    }
  }
}
"""

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

CELL = 11
GAP = 3
STEP = CELL + GAP
DAY_PAD = 32
HEADER_H = 14
MONTH_H = 14
GRID_TOP = HEADER_H + MONTH_H

THEMES = {
    "light": {
        "bg": "#ffffff",
        "text": "#57606a",
        "levels": ["#ebedf0", "#cfe9f6", "#7ecceb", "#2fa8d6", "#0f7fb0"],
    },
    "dark": {
        "bg": "#0d1117",
        "text": "#8b949e",
        "levels": ["#21262d", "#164e63", "#0e7490", "#06b6d4", "#22d3ee"],
    },
}


def fetch_calendar():
    payload = json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Content-Type": "application/json",
            "User-Agent": "profile-heatmap",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def render(calendar, variant):
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]
    theme = THEMES[variant]

    width = DAY_PAD + len(weeks) * STEP + 6
    height = GRID_TOP + 7 * STEP + 8

    parts = []
    parts.append(
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" font-family="-apple-system, BlinkMacSystemFont, '
        'Segoe UI, Helvetica, Arial, sans-serif">' % (width, height, width, height)
    )
    parts.append('<rect width="%d" height="%d" fill="%s"/>' % (width, height, theme["bg"]))
    parts.append(
        '<text x="%d" y="%d" font-size="11" font-weight="600" fill="%s">%s &middot; %d contributions in the last year</text>'
        % (DAY_PAD, HEADER_H - 4, theme["text"], USERNAME, total)
    )

    prev_month = None
    for week_index, week in enumerate(weeks):
        first_date = week["contributionDays"][0]["date"]
        month_key = first_date[:7]
        x = DAY_PAD + week_index * STEP
        if month_key != prev_month:
            label = MONTH_NAMES[int(month_key[5:7]) - 1]
            parts.append(
                '<text x="%.1f" y="%d" font-size="9" fill="%s" text-anchor="middle">%s</text>'
                % (x + CELL / 2, GRID_TOP - 4, theme["text"], label)
            )
            prev_month = month_key
        for day in week["contributionDays"]:
            weekday = datetime(
                int(day["date"][:4]),
                int(day["date"][5:7]),
                int(day["date"][8:10]),
            ).weekday()
            y = GRID_TOP + weekday * STEP
            level = min(max(day["level"], 0), 4)
            parts.append(
                '<rect x="%d" y="%d" width="%d" height="%d" rx="2.5" fill="%s"/>'
                % (x, y, CELL, CELL, theme["levels"][level])
            )

    for i, label in enumerate(["Mon", "Wed", "Fri"]):
        y = GRID_TOP + [0, 2, 4][i] * STEP
        parts.append(
            '<text x="%d" y="%.1f" font-size="9" fill="%s" text-anchor="end">%s</text>'
            % (DAY_PAD - 6, y + CELL / 2 + 3, theme["text"], label)
        )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if not TOKEN:
        raise SystemExit("GITHUB_TOKEN is required")
    calendar = fetch_calendar()
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(out_dir, exist_ok=True)
    for variant in ("light", "dark"):
        path = os.path.join(out_dir, "github-contribution-heatmap-%s.svg" % variant)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render(calendar, variant))
        print("wrote %s" % path)


if __name__ == "__main__":
    main()
