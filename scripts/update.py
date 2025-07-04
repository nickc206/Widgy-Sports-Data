import requests
import json
from datetime import datetime, timedelta
import pytz

PACIFIC_TZ = pytz.timezone("America/Los_Angeles")

# Constants
TOP_CLUBS = [
    "Real Madrid", "Barcelona", "Manchester City", "Manchester United", "Arsenal", "Chelsea", "Liverpool",
    "Bayern Munich", "Borussia Dortmund", "RB Leipzig",
    "Juventus", "Inter Milan", "AC Milan", "Napoli",
    "Paris Saint-Germain", "Marseille",
    "Ajax", "Porto", "Benfica", "Sporting CP",
    "Atlético Madrid", "Sevilla", "Bologna"
]

TOP_COUNTRIES = [
    "Brazil", "Argentina", "France", "Germany", "Spain", "Italy", "England", "Belgium"
]

TEAM_IDS = {
    "seahawks": "26",
    "mariners": "12",
    "kraken": "Seattle Kraken"
}

SOCCER_COMPETITIONS_PRIORITY = [
    "FIFA World Cup", "UEFA European Championship", "UEFA Champions League", "UEFA Europa League",
    "English Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"
]

def fetch_json(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def get_team_game(team_key):
    team_id = TEAM_IDS[team_key]
    if team_key == "kraken":
        url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{team_id}"
    else:
        url = f"https://site.api.espn.com/apis/site/v2/sports/teams/{team_id}"
    data = fetch_json(url)
    events = data.get("team", {}).get("nextEvent", [])
    if not events:
        return blank_game()
    event = events[0]
    competition = event["competitions"][0]
    return parse_event(event, competition)

def get_league_game(league_slug):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{league_slug}/scoreboard"
    data = fetch_json(url)
    events = data.get("events", [])
    if not events:
        return blank_game()
    event = events[0]
    competition = event["competitions"][0]
    return parse_event(event, competition)

def parse_event(event, competition):
    home = competition["competitors"][0]
    away = competition["competitors"][1]
    event_dt = datetime.fromisoformat(event["date"]).astimezone(PACIFIC_TZ)
    return {
        "home_team": home["team"]["displayName"],
        "away_team": away["team"]["displayName"],
        "home_short": home["team"].get("abbreviation", home["team"]["displayName"]),
        "away_short": away["team"].get("abbreviation", away["team"]["displayName"]),
        "home_score": home.get("score", ""),
        "away_score": away.get("score", ""),
        "home_logo": home["team"]["logo"],
        "away_logo": away["team"]["logo"],
        "home_record": home.get("records", [{}])[0].get("summary", ""),
        "away_record": away.get("records", [{}])[0].get("summary", ""),
        "date": event_dt.strftime("%m/%d"),
        "time": event_dt.strftime("%-I:%M %p"),
        "status": competition["status"]["type"]["description"].lower(),
        "is_live": competition["status"]["type"]["state"] == "in",
        "time_left": competition["status"].get("displayClock", ""),
        "quarter": competition["status"].get("period", "")
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

def get_top_soccer_games():
    now = datetime.now(pytz.utc)
    cutoff = now + timedelta(days=3)
    collected_games = []

    # Check top teams first
    for team_name in TOP_CLUBS + TOP_COUNTRIES:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{team_name.lower().replace(' ', '-')}/teams"
        try:
            team_data = fetch_json(url)
            team_id = team_data["sports"][0]["leagues"][0]["teams"][0]["team"]["id"]
            team_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/teams/{team_id}"
            detail_data = fetch_json(team_url)
            events = detail_data.get("team", {}).get("nextEvent", [])
            for event in events:
                event_dt = datetime.fromisoformat(event["date"])
                if event_dt < now or event_dt > cutoff:
                    continue
                competition = event["competitions"][0]
                parsed = parse_event(event, competition)
                collected_games.append(parsed)
                if len(collected_games) >= 3:
                    return collected_games
        except Exception:
            continue

    # If not enough games, fallback to competitions
    for comp in SOCCER_COMPETITIONS_PRIORITY:
        slug = comp.lower().replace(" ", "-").replace("uefa-", "")
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard"
        try:
            data = fetch_json(url)
            for event in data.get("events", []):
                event_dt = datetime.fromisoformat(event["date"])
                if event_dt < now:
                    continue
                competition = event["competitions"][0]
                parsed = parse_event(event, competition)
                collected_games.append(parsed)
                if len(collected_games) >= 3:
                    return collected_games
        except Exception:
            continue

    return collected_games[:3]

def main():
    result = {
        "seahawks": get_team_game("seahawks"),
        "mariners": get_team_game("mariners"),
        "kraken": get_team_game("kraken"),
        "nfl": get_league_game("football/nfl"),
        "nba": get_league_game("basketball/nba"),
        "mlb": get_league_game("baseball/mlb"),
        "nhl": get_league_game("hockey/nhl"),
        "soccer": get_top_soccer_games()
    }

    with open("sports.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()