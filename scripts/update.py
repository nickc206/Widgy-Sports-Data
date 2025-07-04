import requests
import json
from datetime import datetime
from dateutil import parser

def fetch_json(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def get_league_game(sport, league):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"
    data = fetch_json(url)
    events = data.get("events", [])

    for event in events:
        competition = event.get("competitions", [{}])[0]
        status = competition.get("status", {}).get("type", {}).get("name", "")
        competitors = competition.get("competitors", [])

        if len(competitors) != 2:
            continue

        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})

        game_time = competition.get("date")
        event_dt = parser.parse(game_time)
        pacific_dt = event_dt.astimezone().astimezone()  # Simplified timezone handling

        return {
            "home_team": home.get("team", {}).get("displayName", ""),
            "away_team": away.get("team", {}).get("displayName", ""),
            "home_short": home.get("team", {}).get("shortDisplayName", ""),
            "away_short": away.get("team", {}).get("shortDisplayName", ""),
            "home_score": home.get("score", ""),
            "away_score": away.get("score", ""),
            "home_logo": home.get("team", {}).get("logos", [{}])[0].get("href", ""),
            "away_logo": away.get("team", {}).get("logos", [{}])[0].get("href", ""),
            "home_record": home.get("records", [{}])[0].get("summary", ""),
            "away_record": away.get("records", [{}])[0].get("summary", ""),
            "date": pacific_dt.strftime("%m/%d"),
            "time": pacific_dt.strftime("%-I:%M %p"),
            "status": status.lower(),
            "is_live": status.lower() == "in",
            "time_left": competition.get("status", {}).get("displayClock", ""),
            "quarter": competition.get("status", {}).get("period", "")
        }

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
    output = {
        "nfl": get_league_game("football", "nfl"),
        "nba": get_league_game("basketball", "nba"),
        "mlb": get_league_game("baseball", "mlb"),
        "nhl": get_league_game("hockey", "nhl")
    }

    with open("sports.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()