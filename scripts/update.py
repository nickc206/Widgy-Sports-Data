import requests
import json
from datetime import datetime
from dateutil import parser, tz

PACIFIC = tz.gettz("America/Los_Angeles")

def fetch_json(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

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

def parse_game(event):
    competition = event["competitions"][0]
    competitors = competition["competitors"]
    home = next(c for c in competitors if c["homeAway"] == "home")
    away = next(c for c in competitors if c["homeAway"] == "away")

    event_dt = parser.parse(event["date"]).astimezone(PACIFIC)

    return {
        "home_team": home["team"]["displayName"],
        "away_team": away["team"]["displayName"],
        "home_short": home["team"]["shortDisplayName"],
        "away_short": away["team"]["shortDisplayName"],
        "home_score": home.get("score", ""),
        "away_score": away.get("score", ""),
        "home_logo": home["team"].get("logos", [{}])[0].get("href", ""),
        "away_logo": away["team"].get("logos", [{}])[0].get("href", ""),
        "home_record": home.get("records", [{}])[0].get("summary", ""),
        "away_record": away.get("records", [{}])[0].get("summary", ""),
        "date": event_dt.strftime("%m/%d"),
        "time": event_dt.strftime("%-I:%M %p"),
        "status": event["status"]["type"]["description"].lower(),
        "is_live": event["status"]["type"]["state"] == "in",
        "time_left": competition.get("status", {}).get("displayClock", ""),
        "quarter": competition.get("status", {}).get("period", "")
    }

def get_next_game(sport, league):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"
    data = fetch_json(url)
    events = data.get("events", [])

    future = []
    now = datetime.now(tz=tz.UTC)

    for event in events:
        try:
            dt = parser.parse(event["date"])
            if dt > now:
                future.append((dt, event))
        except:
            continue

    if not future:
        return blank_game()

    # Sort by datetime and pick the first
    future.sort(key=lambda x: x[0])
    return parse_game(future[0][1])

def main():
    output = {
        "nfl": get_next_game("football", "nfl"),
        "nba": get_next_game("basketball", "nba"),
        "mlb": get_next_game("baseball", "mlb"),
        "nhl": get_next_game("hockey", "nhl"),
        "seahawks": blank_game(),  # Not yet fixed
        "mariners": blank_game(),  # Not yet fixed
        "kraken": blank_game(),    # Not yet fixed
        "soccer": []               # Placeholder
    }

    with open("sports.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()