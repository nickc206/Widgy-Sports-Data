import requests
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
    if not events:
        return blank_game()

    event = events[0]
    competitions = event.get("competitions", [{}])
    if not competitions:
        return blank_game()

    comp = competitions[0]
    home = comp.get("competitors", [])[0]
    away = comp.get("competitors", [])[1]
    status = comp.get("status", {}).get("type", {}).get("description", "scheduled")
    is_live = status.lower() == "in progress"

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
        "time_left": comp.get("status", {}).get("displayClock", ""),
        "quarter": comp.get("status", {}).get("period", "")
    }

def get_team_game(team_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}"
    data = fetch_json(url)

    events = data.get("team", {}).get("nextEvent", [])
    if not events:
        return blank_game()

    event = events[0]
    comp = event.get("competitions", [{}])[0]
    home = comp.get("competitors", [])[0]
    away = comp.get("competitors", [])[1]
    status = comp.get("status", {}).get("type", {}).get("description", "scheduled")
    is_live = status.lower() == "in progress"

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
        "nfl": get_league_game("football", "nfl"),
        "nba": get_league_game("basketball", "nba"),
        "mlb": get_league_game("baseball", "mlb"),
        "nhl": get_league_game("hockey", "nhl"),
        "seahawks": get_team_game("26")  # numeric ID for Seahawks
    }

    import json
    with open("sports.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()
    