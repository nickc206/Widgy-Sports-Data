import requests
import json
from datetime import datetime
import pytz

def fetch_json(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()

def format_time(dt_str):
    dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%MZ")
    dt = dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("US/Pacific"))
    return dt.strftime("%I:%M %p").lstrip("0")

def format_date(dt_str):
    dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%MZ")
    dt = dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("US/Pacific"))
    return dt.strftime("%m/%d")

def get_team_game(team_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/teams/{team_id}"
    data = fetch_json(url)

    events = data.get("team", {}).get("nextEvent", [])
    if not events:
        return empty_game()

    event = events[0]
    competition = event["competitions"][0]
    status = competition["status"]["type"]["name"]
    is_live = status == "STATUS_IN_PROGRESS"

    home = competition["competitors"][0] if competition["competitors"][0]["homeAway"] == "home" else competition["competitors"][1]
    away = competition["competitors"][1] if competition["competitors"][0]["homeAway"] == "home" else competition["competitors"][0]

    event_dt = datetime.strptime(event["date"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=pytz.utc).astimezone(pytz.timezone("US/Pacific"))

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
        "time": event_dt.strftime("%I:%M %p").lstrip("0"),
        "status": status.lower(),
        "is_live": is_live,
        "time_left": competition["status"].get("displayClock", ""),
        "quarter": competition["status"].get("period", 0)
    }

def get_league_game(sport, league):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"
    data = fetch_json(url)
    events = data.get("events", [])
    if not events:
        return empty_game()

    event = events[0]
    competition = event["competitions"][0]
    status = competition["status"]["type"]["name"]
    is_live = status == "STATUS_IN_PROGRESS"

    home = competition["competitors"][0] if competition["competitors"][0]["homeAway"] == "home" else competition["competitors"][1]
    away = competition["competitors"][1] if competition["competitors"][0]["homeAway"] == "home" else competition["competitors"][0]

    event_dt = datetime.strptime(event["date"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=pytz.utc).astimezone(pytz.timezone("US/Pacific"))

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
        "time": event_dt.strftime("%I:%M %p").lstrip("0"),
        "status": status.lower(),
        "is_live": is_live,
        "time_left": competition["status"].get("displayClock", ""),
        "quarter": competition["status"].get("period", 0)
    }

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
    result = {
        # Seahawks = team ID 26
        "seahawks": get_team_game("26"),
        "mariners": get_team_game("21"),
        "kraken": get_team_game("90"),
        "nfl": get_league_game("football", "nfl"),
        "nba": get_league_game("basketball", "nba"),
        "mlb": get_league_game("baseball", "mlb"),
        "nhl": get_league_game("hockey", "nhl"),
        "soccer": []  # placeholder
    }

    with open("sports.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()