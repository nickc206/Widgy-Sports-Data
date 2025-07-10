import requests
import json
from datetime import datetime
from dateutil import parser
import pytz

def fetch_json(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def get_next_game(sport, league):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"
    data = fetch_json(url)
    events = data.get("events", [])
    if not events:
        return blank_game()

    future = []
    for event in events:
        dt = parser.parse(event["date"])
        if dt > datetime.now(pytz.utc):
            comp = event["competitions"][0]
            clock = comp.get("status", {}).get("displayClock", "").lower()
            if "tbd" not in clock:
                future.append((dt, event))

    if not future:
        return blank_game()

    future.sort()
    _, event = future[0]
    comp = event["competitions"][0]
    home = comp["competitors"][0]
    away = comp["competitors"][1]

    event_dt = parser.parse(event["date"])
    home_score = home.get("score", "0")
    away_score = away.get("score", "0")

    return {
        "home_team": home["team"]["displayName"],
        "away_team": away["team"]["displayName"],
        "home_short": home["team"]["shortDisplayName"],
        "away_short": away["team"]["shortDisplayName"],
        "home_score": home_score,
        "away_score": away_score,
        "home_logo": home["team"].get("logos", [{}])[0].get("href", ""),
        "away_logo": away["team"].get("logos", [{}])[0].get("href", ""),
        "home_record": home.get("records", [{}])[0].get("summary", ""),
        "away_record": away.get("records", [{}])[0].get("summary", ""),
        "date": event_dt.astimezone(pytz.timezone("US/Pacific")).strftime("%m/%d"),
        "time": event_dt.astimezone(pytz.timezone("US/Pacific")).strftime("%-I:%M %p"),
        "status": event["status"]["type"]["description"].lower(),
        "is_live": event["status"]["type"]["state"] == "in",
        "time_left": comp.get("status", {}).get("displayClock", ""),
        "quarter": comp.get("status", {}).get("period", "")
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
    output = {
        "nfl": get_next_game("football", "nfl"),
        "nba": get_next_game("basketball", "nba"),
        "mlb": get_next_game("baseball", "mlb"),
        "nhl": get_next_game("hockey", "nhl"),
        "seahawks": blank_game(),  # Placeholder
        "mariners": blank_game(),  # Placeholder
        "kraken": blank_game(),    # Placeholder
        "soccer": []               # Placeholder
    }

    with open("sports.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()