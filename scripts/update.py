import requests
import json
from datetime import datetime
from pytz import timezone

def fetch_json(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def get_league_game(sport, league):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"
    data = fetch_json(url)
    events = data.get("events", [])
    for event in events:
        comp = event["competitions"][0]
        home = next(t for t in comp["competitors"] if t["homeAway"] == "home")
        away = next(t for t in comp["competitors"] if t["homeAway"] == "away")
        status = comp["status"]["type"]["name"]
        is_live = comp["status"]["type"]["state"] == "in"
        game_clock = comp["status"].get("displayClock", "")
        game_period = comp["status"].get("period", "")
        event_dt = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).astimezone(timezone("US/Pacific"))

        return {
            "home_team": home["team"]["displayName"],
            "away_team": away["team"]["displayName"],
            "home_short": home["team"].get("shortDisplayName", ""),
            "away_short": away["team"].get("shortDisplayName", ""),
            "home_score": home.get("score", ""),
            "away_score": away.get("score", ""),
            "home_logo": home["team"].get("logos", [{}])[0].get("href", ""),
            "away_logo": away["team"].get("logos", [{}])[0].get("href", ""),
            "home_record": home.get("records", [{}])[0].get("summary", ""),
            "away_record": away.get("records", [{}])[0].get("summary", ""),
            "date": event_dt.strftime("%m/%d"),
            "time": event_dt.strftime("%-I:%M %p"),
            "status": status.lower(),
            "is_live": is_live,
            "time_left": game_clock,
            "quarter": game_period
        }

    return blank_game()

def get_team_game(team_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}"
    data = fetch_json(url)
    next_event = data.get("team", {}).get("nextEvent", [])
    if not next_event:
        return blank_game()
    event = next_event[0]
    comp = event["competitions"][0]
    home = next(t for t in comp["competitors"] if t["homeAway"] == "home")
    away = next(t for t in comp["competitors"] if t["homeAway"] == "away")
    status = comp["status"]["type"]["name"]
    is_live = comp["status"]["type"]["state"] == "in"
    game_clock = comp["status"].get("displayClock", "")
    game_period = comp["status"].get("period", "")
    event_dt = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).astimezone(timezone("US/Pacific"))

    return {
        "home_team": home["team"]["displayName"],
        "away_team": away["team"]["displayName"],
        "home_short": home["team"].get("shortDisplayName", ""),
        "away_short": away["team"].get("shortDisplayName", ""),
        "home_score": home.get("score", ""),
        "away_score": away.get("score", ""),
        "home_logo": home["team"].get("logos", [{}])[0].get("href", ""),
        "away_logo": away["team"].get("logos", [{}])[0].get("href", ""),
        "home_record": home.get("records", [{}])[0].get("summary", ""),
        "away_record": away.get("records", [{}])[0].get("summary", ""),
        "date": event_dt.strftime("%m/%d"),
        "time": event_dt.strftime("%-I:%M %p"),
        "status": status.lower(),
        "is_live": is_live,
        "time_left": game_clock,
        "quarter": game_period
    }

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

def main():
    result = {
        "nfl": get_league_game("football", "nfl"),
        "nba": get_league_game("basketball", "nba"),
        "mlb": get_league_game("baseball", "mlb"),
        "nhl": get_league_game("hockey", "nhl"),
        "seahawks": get_team_game("26")
    }

    with open("sports.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()