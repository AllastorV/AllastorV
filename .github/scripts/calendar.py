import json
import os
import sys
import urllib.request
from datetime import date

LOGIN = "AllastorV"
LEVELS = {
    "NONE": "#3d2a1f",
    "FIRST_QUARTILE": "#f3e4d0",
    "SECOND_QUARTILE": "#f0b429",
    "THIRD_QUARTILE": "#e07b39",
    "FOURTH_QUARTILE": "#d9432f",
}
WIDTH, PAD, LEFT, GAP, TOP = 880, 16, 50, 3, 70
QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{date weekday contributionCount contributionLevel}}}}}}"""


def fetch(token):
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def render(cal):
    weeks = cal["weeks"]
    width = WIDTH
    step = (width - LEFT - PAD + GAP) / len(weeks)
    cell = round(step - GAP, 2)
    right = LEFT + len(weeks) * step - GAP
    height = round(TOP + 7 * step + 46)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" '
        f'aria-label="{cal["totalContributions"]} contributions in the last year">',
        "<style>text{font-family:Georgia,'Iowan Old Style','Palatino Linotype',serif;fill:#d8b48a}</style>",
        f'<rect width="{width}" height="{height}" rx="14" fill="#2b1d16"/>',
        f'<text x="{PAD}" y="36" font-size="18" fill="#f3e4d0" style="fill:#f3e4d0">'
        f'{cal["totalContributions"]} contributions in the last year</text>',
    ]
    last_month = None
    for i, week in enumerate(weeks):
        x = round(LEFT + i * step, 2)
        first = date.fromisoformat(week["contributionDays"][0]["date"])
        if first.month != last_month and i < len(weeks) - 2:
            if last_month is not None or first.day <= 7:
                out.append(f'<text x="{x}" y="{TOP - 10}" font-size="13">{first.strftime("%b").lower()}</text>')
            last_month = first.month
        for d in week["contributionDays"]:
            y = round(TOP + d["weekday"] * step, 2)
            out.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{LEVELS[d["contributionLevel"]]}">'
                f'<title>{d["date"]}: {d["contributionCount"]}</title></rect>'
            )
    for row, label in ((1, "mon"), (3, "wed"), (5, "fri")):
        out.append(f'<text x="{PAD}" y="{round(TOP + row * step + cell - 1, 2)}" font-size="13">{label}</text>')
    ly = round(TOP + 7 * step + 14, 2)
    more_x = right
    sw_end = more_x - 40
    sw_start = sw_end - 5 * step + GAP
    out.append(f'<text x="{round(more_x, 2)}" y="{round(ly + cell - 1, 2)}" font-size="13" text-anchor="end">more</text>')
    for j, color in enumerate(LEVELS.values()):
        out.append(f'<rect x="{round(sw_start + j * step, 2)}" y="{ly}" width="{cell}" height="{cell}" rx="2" fill="{color}"/>')
    out.append(f'<text x="{round(sw_start - 8, 2)}" y="{round(ly + cell - 1, 2)}" font-size="13" text-anchor="end">less</text>')
    out.append("</svg>")
    return "\n".join(out)


def self_check():
    cal = {
        "totalContributions": 3,
        "weeks": [{"contributionDays": [
            {"date": "2026-01-04", "weekday": 0, "contributionCount": 0, "contributionLevel": "NONE"},
            {"date": "2026-01-05", "weekday": 1, "contributionCount": 3, "contributionLevel": "FOURTH_QUARTILE"},
        ]}] * 3,
    }
    svg = render(cal)
    assert svg.count("<title>") == 6
    assert "#d9432f" in svg and "3 contributions" in svg


if __name__ == "__main__":
    self_check()
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GH_TOKEN is not set")
    path = sys.argv[1] if len(sys.argv) > 1 else "contributions.svg"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(fetch(token)))
