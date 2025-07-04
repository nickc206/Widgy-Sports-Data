import json
import requests
from datetime import datetime
from dateutil import parser

def fetch_json(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def safe_logo(team):
    try:
        return team["logos"][0]["href"]
    except (KeyError, IndexError, TypeError):
        return ""

def format_game(event, sport_type):
    competitions = event.get("competitions", [{}])[0]
    competitors = competitions.get("competitors", [])
    if len(competitors) != 2:
        return None

    home = next((c for c in competitors if c.get("homeAway") == "home"), {})
    away = next((c for c in competitors if c.get("homeAway") == "away"), {})

    event_dt = parser.parse(event["date"])
    pacific = event_dt.astimezone()
    time_str = pacific.strftime("%-I:%M %p")
    date_str = pacific.strftime("%m/%d")

    status_info = competitions.get("status", {}).get("type", {})
    is_live = status_info.get("state") == "in"

    return {
        "home_team": home.get("team", {}).get("displayName", ""),
        "away_team": away.get("team", {}).get("displayName", ""),
        "home_short": home.get("team", {}).get("shortDisplayName", ""),
        "away_short": away.get("team", {}).get("shortDisplayName", ""),
        "home_score": home.get("score", ""),
        "away_score": away.get("score", ""),
        "home_logo": safe_logo(home.get("team", {})),
        "away_logo": safe_logo(away.get("team", {})),
        "home_record": home.get("records", [{}])[0].get("summary", ""),
        "away_record": away.get("records", [{}])[0].get("summary", ""),
        "date": date_str,
        "time": time_str,
        "status": status_info.get("description", "scheduled").lower(),
        "is_live": is_live,
        "time_left": competitions.get("status", {}).get("displayClock", ""),
        "quarter": competitions.get("status", {}).get("period", 0),
    }

def get_team_game(team_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/teams/{team_id}"
    data = fetch_json(url)
    events = data.get("team", {}).get("nextEvent", [])
    if not events:
        return empty_game()
    return format_game(events[0], data.get("sport", {}).get("name", "")) or empty_game()

def get_league_game(sport, league):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"
    data = fetch_json(url)
    events = data.get("events", [])
    for event in events:
        game = format_game(event, sport)
        if game:
            return game
    return empty_game()

def empty_game():
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
    data = {
        "seahawks": get_team_game("sea"),
        "mariners": get_team_game("sea"),
        "kraken": get_team_game("sea"),
        "nfl": get_league_game("football", "nfl"),
        "nba": get_league_game("basketball", "nba"),
        "mlb": get_league_game("baseball", "mlb"),
        "nhl": get_league_game("hockey", "nhl"),
        "soccer": []  # will be filled next step
    }
    with open("sports.json", "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()