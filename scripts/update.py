import requests
import json
from datetime import datetime, timedelta
from dateutil import parser
import pytz

pst = pytz.timezone("America/Los_Angeles")
now = datetime.now(pst)

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

def parse_event(event):
    comp = event["competitions"][0]
    home = comp["competitors"][0]
    away = comp["competitors"][1]
    event_dt = parser.parse(event["date"]).astimezone(pst)

    status = event["status"]["type"]
    is_live = status["state"] == "in"
    is_final = status["completed"]

    show_final_today = is_final and event_dt.date() == now.date()

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
        "time": "" if "TBD" in status.get("description", "") else event_dt.strftime("%-I:%M %p"),
        "status": status["description"].lower(),
        "is_live": is_live,
        "time_left": comp.get("status", {}).get("displayClock", ""),
        "quarter": comp.get("status", {}).get("period", ""),
    }

def get_next_game(sport, league):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"
    data = fetch_json(url)
    events = data.get("events", [])
    future = []

    for event in events:
        try:
            event_dt = parser.parse(event["date"]).astimezone(pst)
            status = event["status"]["type"]
            if event_dt >= now or (status["completed"] and event_dt.date() == now.date()):
                future.append((event_dt, event))
        except:
            continue

    if not future:
        return blank_game()

    future.sort(key=lambda x: x[0])  # Sort by datetime
    return parse_event(future[0][1])

def main():
    data = {
        "nfl": get_next_game("football", "nfl"),
        "nba": get_next_game("basketball", "nba"),
        "mlb": get_next_game("baseball", "mlb"),
        "nhl": get_next_game("hockey", "nhl")
    }

    with open("sports.json", "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()