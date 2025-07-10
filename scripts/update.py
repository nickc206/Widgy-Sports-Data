import requests
import json
from datetime import datetime
from dateutil import parser
import pytz

PST = pytz.timezone("US/Pacific")

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

    now_utc = datetime.now(pytz.utc)
    future = []
    for event in events:
        try:
            dt = parser.parse(event["date"])
            if dt > now_utc:
                comp = event["competitions"][0]
                clock = comp.get("status", {}).get("displayClock", "").lower()
                future.append({
                    "datetime": dt,
                    "event": event
                })
        except Exception:
            continue

    if not future:
        return blank_game()

    future.sort(key=lambda x: x["datetime"])
    chosen = future[0]["event"]
    comp = chosen["competitions"][0]
    home = comp["competitors"][0]
    away = comp["competitors"][1]
    event_dt = parser.parse(chosen["date"]).astimezone(PST)

    return {
        "home_team": home["team"]["displayName"],
        "away_team": away["team"]["displayName"],
        "home_short": home["team"]["shortDisplayName"],
        "away_short": away["team"]["shortDisplayName"],
        "home_score": home.get("score", "0"),
        "away_score": away.get("score", "0"),
        "home_logo": home["team"].get("logos", [{}])[0].get("href", ""),
        "away_logo": away["team"].get("logos", [{}])[0].get("href", ""),
        "home_record": home.get("records", [{}])[0].get("summary", ""),
        "away_record": away.get("records", [{}])[0].get("summary", ""),
        "date": event_dt.strftime("%m/%d"),
        "time": event_dt.strftime("%-I:%M %p"),
        "status": chosen["status"]["type"]["description"].lower(),
        "is_live": chosen["status"]["type"]["state"] == "in",
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
        "seahawks": blank_game(),
        "mariners": blank_game(),
        "kraken": blank_game(),
        "soccer": []
    }

    with open("sports.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()