import requests
import json
from datetime import datetime, timedelta

# ESPN team IDs (team-specific endpoint)
TEAM_IDS = {
    "seahawks": ("football", "nfl", "sea"),
    "mariners": ("baseball", "mlb", "sea"),
    "kraken": ("hockey", "nhl", "sea")
}

def fetch_json(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def get_team_game(team_key):
    try:
        sport, league, abbr = TEAM_IDS[team_key]
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams/{abbr}"
        data = fetch_json(url)
        events = data.get("team", {}).get("nextEvent", [])
        if not events:
            return blank_game()
        event = events[0]
        competition = event["competitions"][0]
        competitors = competition["competitors"]
        home = next(c for c in competitors if c["homeAway"] == "home")
        away = next(c for c in competitors if c["homeAway"] == "away")
        event_dt = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
        status = competition["status"]["type"]["name"].lower()
        return {
            "home_team": home["team"]["displayName"],
            "away_team": away["team"]["displayName"],
            "home_short": home["team"]["shortDisplayName"],
            "away_short": away["team"]["shortDisplayName"],
            "home_score": home.get("score", "0"),
            "away_score": away.get("score", "0"),
            "home_logo": home["team"]["logos"][0]["href"],
            "away_logo": away["team"]["logos"][0]["href"],
            "home_record": home.get("records", [{}])[0].get("summary", ""),
            "away_record": away.get("records", [{}])[0].get("summary", ""),
            "date": event_dt.strftime("%m/%d"),
            "time": event_dt.strftime("%-I:%M %p"),
            "status": status if status in ["in progress", "final"] else "scheduled",
            "is_live": status == "in progress",
            "time_left": competition["status"].get("displayClock", ""),
            "quarter": competition["status"].get("period", "")
        }
    except Exception as e:
        print(f"Error fetching {team_key}: {e}")
        return blank_game()

def blank_game():
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

def placeholder_league_game():
    return blank_game()

def placeholder_soccer():
    return []

def main():
    data = {
        "seahawks": get_team_game("seahawks"),
        "mariners": get_team_game("mariners"),
        "kraken": get_team_game("kraken"),
        "nfl": placeholder_league_game(),
        "nba": placeholder_league_game(),
        "mlb": placeholder_league_game(),
        "nhl": placeholder_league_game(),
        "soccer": placeholder_soccer()
    }

    with open("sports.json", "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()