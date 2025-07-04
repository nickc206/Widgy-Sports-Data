import requests
import json
from datetime import datetime, timedelta
import pytz
import os

PACIFIC_TZ = pytz.timezone("US/Pacific")

# --- Configuration ---
SOCCER_TOP_CLUBS = {
    "Real Madrid", "Barcelona", "Manchester City", "Manchester United", "Liverpool",
    "Arsenal", "Chelsea", "Tottenham Hotspur", "Bayern Munich", "Borussia Dortmund",
    "PSG", "Juventus", "Inter Milan", "AC Milan", "Napoli", "Atletico Madrid",
    "Ajax", "Porto", "Benfica", "Marseille", "RB Leipzig", "Leverkusen", "Roma",
    "Sevilla", "Feyenoord", "Sporting CP", "Bologna"
}

TOP_INTL_TEAMS = {
    "France", "Brazil", "Argentina", "Germany", "England",
    "Spain", "Italy", "Portugal", "Netherlands", "Belgium"
}

SOCCER_LEAGUE_SLUGS = [
    "eng.1", "esp.1", "ita.1", "ger.1", "fra.1",
    "uefa.champions", "uefa.europa", "fifa.world", "uefa.euro"
]

TEAM_ABBRS = {
    "seahawks": "sea",
    "mariners": "sea",
    "kraken": "sea"
}

LEAGUE_SLUGS = {
    "nfl": "nfl",
    "nba": "nba",
    "mlb": "mlb",
    "nhl": "nhl"
}

def fetch_json(url):
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def convert_utc_to_pacific(utc_string):
    utc_dt = datetime.fromisoformat(utc_string.replace("Z", "+00:00"))
    local_dt = utc_dt.astimezone(PACIFIC_TZ)
    return local_dt.strftime("%m/%d"), local_dt.strftime("%-I:%M %p")

def safe_get(d, *keys):
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return ""
    return d or ""

def get_team_game(team_abbr):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_abbr}"
    data = fetch_json(url)
    team = data.get("team", {})
    next_event = team.get("nextEvent", [{}])[0]

    if not next_event or "competitions" not in next_event:
        return empty_game_dict()

    comp = next_event["competitions"][0]
    competitors = comp["competitors"]
    home = next(c for c in competitors if c["homeAway"] == "home")
    away = next(c for c in competitors if c["homeAway"] == "away")

    date, time = convert_utc_to_pacific(next_event["date"])
    return {
        "home_team": home["team"]["displayName"],
        "away_team": away["team"]["displayName"],
        "home_short": home["team"]["shortDisplayName"],
        "away_short": away["team"]["shortDisplayName"],
        "home_score": home.get("score", ""),
        "away_score": away.get("score", ""),
        "home_logo": safe_get(home, "team", "logos", 0, "href"),
        "away_logo": safe_get(away, "team", "logos", 0, "href"),
        "home_record": safe_get(home, "records", 0, "summary"),
        "away_record": safe_get(away, "records", 0, "summary"),
        "date": date,
        "time": time,
        "status": next_event.get("status", {}).get("type", {}).get("description", "scheduled").lower(),
        "is_live": next_event.get("status", {}).get("type", {}).get("state", "") == "in",
        "time_left": next_event.get("status", {}).get("displayClock", ""),
        "quarter": next_event.get("status", {}).get("period", "")
    }

def get_league_game(league_slug):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{league_slug}/scoreboard"
    data = fetch_json(url)
    events = data.get("events", [])
    if not events:
        return empty_game_dict()

    event = events[0]
    comp = event["competitions"][0]
    competitors = comp["competitors"]
    home = next(c for c in competitors if c["homeAway"] == "home")
    away = next(c for c in competitors if c["homeAway"] == "away")

    date, time = convert_utc_to_pacific(event["date"])
    return {
        "home_team": home["team"]["displayName"],
        "away_team": away["team"]["displayName"],
        "home_short": home["team"]["shortDisplayName"],
        "away_short": away["team"]["shortDisplayName"],
        "home_score": home.get("score", ""),
        "away_score": away.get("score", ""),
        "home_logo": safe_get(home, "team", "logos", 0, "href"),
        "away_logo": safe_get(away, "team", "logos", 0, "href"),
        "home_record": safe_get(home, "records", 0, "summary"),
        "away_record": safe_get(away, "records", 0, "summary"),
        "date": date,
        "time": time,
        "status": event.get("status", {}).get("type", {}).get("description", "scheduled").lower(),
        "is_live": event.get("status", {}).get("type", {}).get("state", "") == "in",
        "time_left": event.get("status", {}).get("displayClock", ""),
        "quarter": event.get("status", {}).get("period", "")
    }

def get_top_soccer_games():
    results = []
    seen = set()
    now = datetime.now(pytz.utc)
    max_days = 3
    max_delta = timedelta(days=max_days)

    for slug in SOCCER_LEAGUE_SLUGS:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard"
        try:
            data = fetch_json(url)
        except Exception:
            continue

        for event in data.get("events", []):
            try:
                event_dt = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).astimezone(pytz.utc)
                if event_dt < now or event_dt - now > timedelta(days=30):
                    continue

                comp = event["competitions"][0]
                competitors = comp["competitors"]
                home = next(c for c in competitors if c["homeAway"] == "home")
                away = next(c for c in competitors if c["homeAway"] == "away")
                home_name = home["team"]["displayName"]
                away_name = away["team"]["displayName"]

                top_priority = (
                    home_name in SOCCER_TOP_CLUBS or away_name in SOCCER_TOP_CLUBS or
                    home_name in TOP_INTL_TEAMS or away_name in TOP_INTL_TEAMS
                )

                if (home_name, away_name) in seen or (away_name, home_name) in seen:
                    continue

                seen.add((home_name, away_name))

                date, time = convert_utc_to_pacific(event["date"])
                results.append({
                    "home_team": home_name,
                    "away_team": away_name,
                    "home_short": home["team"]["shortDisplayName"],
                    "away_short": away["team"]["shortDisplayName"],
                    "home_score": home.get("score", ""),
                    "away_score": away.get("score", ""),
                    "home_logo": safe_get(home, "team", "logos", 0, "href"),
                    "away_logo": safe_get(away, "team", "logos", 0, "href"),
                    "home_record": safe_get(home, "records", 0, "summary"),
                    "away_record": safe_get(away, "records", 0, "summary"),
                    "date": date,
                    "time": time,
                    "status": event.get("status", {}).get("type", {}).get("description", "scheduled").lower(),
                    "is_live": event.get("status", {}).get("type", {}).get("state", "") == "in",
                    "time_left": event.get("status", {}).get("displayClock", ""),
                    "quarter": event.get("status", {}).get("period", ""),
                    "priority": 1 if top_priority and (event_dt - now <= max_delta) else 2 if top_priority else 3
                })
            except Exception:
                continue

    results.sort(key=lambda g: (g["priority"], datetime.strptime(g["date"], "%m/%d")))
    return results[:3]

def empty_game_dict():
    return {
        "home_team": "",
        "away_team": "",
        "home_short": "",
        "away_short": "",
        "home_score": "",
        "away_score": "",
        "home_logo": "",
        "away_logo": "",
        "home_record": "",
        "away_record": "",
        "date": "",
        "time": "",
        "status": "scheduled",
        "is_live": False,
        "time_left": "",
        "quarter": ""
    }

def main():
    result = {}

    # Seahawks, Mariners, Kraken
    for key in ["seahawks", "mariners", "kraken"]:
        try:
            abbr = TEAM_ABBRS[key]
            result[key] = get_team_game(abbr)
        except Exception:
            result[key] = empty_game_dict()

    # NFL, NBA, NHL, MLB
    for league_key, slug in LEAGUE_SLUGS.items():
        try:
            result[league_key] = get_league_game(slug)
        except Exception:
            result[league_key] = empty_game_dict()

    # Top soccer games
    try:
        result["soccer"] = get_top_soccer_games()
    except Exception:
        result["soccer"] = []

    with open("sports.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()