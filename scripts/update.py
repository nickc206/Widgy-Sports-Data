import requests
import json
from datetime import datetime
from dateutil import parser
import pytz

PACIFIC = pytz.timezone("US/Pacific")

def fetch_json(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def format_date_time_utc(utc_str):
    dt_utc = parser.parse(utc_str).astimezone(pytz.utc)
    dt_pst = dt_utc.astimezone(PACIFIC)
    return dt_pst.strftime("%m/%d"), dt_pst.strftime("%-I:%M %p")

def get_league_game(sport, league):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"
    data = fetch_json(url)
    events = data.get("events", [])
    future_events = []

    now = datetime.now(pytz.utc)
    for event in events:
        try:
            event_dt = parser.parse(event["date"])
            if event_dt >= now:
                future_events.append((event_dt, event))
        except:
            continue

    if not future_events:
        return blank_game()

    future_events.sort(key=lambda x: x[0])
    event = future_events[0][1]
    competition = event["competitions"][0]
    home = competition["competitors"][0]
    away = competition["competitors"][1]

    home_score = home.get("score", "0")
    away_score = away.get("score", "0")
    date_str, time_str = format_date_time_utc(event["date"])

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
        "date": date_str,
        "time": time_str,
        "status": event["status"]["type"]["description"].lower(),
        "is_live": event["status"]["type"]["state"] == "in",
        "time_left": competition.get("status", {}).get("displayClock", ""),
        "quarter": competition.get("status", {}).get("period", "")
    }

def get_team_game(team_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}"
    data = fetch_json(url)
    next_event = data["team"].get("nextEvent", [])
    if not next_event:
        return blank_game()

    event = next_event[0]
    competition = event["competitions"][0]
    home = competition["competitors"][0]
    away = competition["competitors"][1]

    home_score = home.get("score", "0")
    away_score = away.get("score", "0")
    date_str, time_str = format_date_time_utc(event["date"])

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
        "date": date_str,
        "time": time_str,
        "status": event["status"]["type"]["description"].lower(),
        "is_live": event["status"]["type"]["state"] == "in",
        "time_left": competition.get("status", {}).get("displayClock", ""),
        "quarter": competition.get("status", {}).get("period", "")
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
        "nfl": get_league_game("football", "nfl"),
        "nba": get_league_game("basketball", "nba"),
        "mlb": get_league_game("baseball", "mlb"),
        "nhl": get_league_game("hockey", "nhl"),
        "seahawks": blank_game(),  # placeholder
        "mariners": blank_game(),  # placeholder
        "kraken": blank_game(),    # placeholder
        "soccer": []               # placeholder
    }

    with open("sports.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()