import requests
import json
from datetime import datetime, timedelta
import pytz

PACIFIC = pytz.timezone("America/Los_Angeles")

# List of teams to always include
TEAMS = {
    "seahawks": "sea",
    "mariners": "sea",
    "kraken": "sea"
}

# League slugs for top game by league
LEAGUES = {
    "nfl": "nfl",
    "nba": "nba",
    "nhl": "nhl",
    "mlb": "mlb"
}

# Prioritized competitions
TOP_TOURNAMENTS = [
    "UEFA Champions League",
    "FIFA World Cup",
    "UEFA European Championship",
    "FIFA Club World Cup"
]

# Top teams per league
TOP_CLUBS = [
    "Real Madrid", "Barcelona", "Atletico Madrid",
    "Manchester City", "Manchester United", "Liverpool", "Arsenal", "Chelsea", "Tottenham Hotspur",
    "Bayern Munich", "Borussia Dortmund", "RB Leipzig",
    "Juventus", "Inter Milan", "AC Milan", "Napoli",
    "PSG", "Marseille", "Monaco",
    "Ajax", "Porto", "Benfica",
    "Bologna"
]

def fetch_json(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def get_team_game(abbr, include_record=False):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{abbr}"
    data = fetch_json(url)
    team = data.get("team", {})
    events = team.get("nextEvent", [])
    if not events:
        return empty_game()
    game = parse_event(events[0], include_record=include_record)
    return game

def parse_event(event, include_record=False):
    competition = event["competitions"][0]
    status = competition["status"]["type"]["description"].lower()
    home = competition["competitors"][0 if competition["competitors"][0]["homeAway"] == "home" else 1]
    away = competition["competitors"][1 if home == competition["competitors"][0] else 0]
    date = datetime.fromisoformat(event["date"]).astimezone(PACIFIC)

    return {
        "home_team": home["team"]["displayName"],
        "away_team": away["team"]["displayName"],
        "home_short": home["team"].get("shortDisplayName", home["team"]["displayName"]),
        "away_short": away["team"].get("shortDisplayName", away["team"]["displayName"]),
        "home_score": home.get("score", ""),
        "away_score": away.get("score", ""),
        "home_logo": home["team"]["logo"],
        "away_logo": away["team"]["logo"],
        "home_record": home["records"][0]["summary"] if include_record and "records" in home else "",
        "away_record": away["records"][0]["summary"] if include_record and "records" in away else "",
        "date": date.strftime("%m/%d"),
        "time": date.strftime("%-I:%M %p"),
        "status": status,
        "is_live": status == "in progress",
        "time_left": competition["status"].get("displayClock", ""),
        "quarter": competition["status"].get("period", "")
    }

def get_league_game(league_slug):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{league_slug}/scoreboard"
    data = fetch_json(url)
    events = data.get("events", [])
    if not events:
        return empty_game()
    return parse_event(events[0])

def get_soccer_games():
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard"
    data = fetch_json(url)
    now = datetime.now(pytz.utc)
    future_games = []
    for event in data.get("events", []):
        comp = event.get("competitions", [{}])[0]
        date_str = event.get("date")
        if not date_str:
            continue
        date = datetime.fromisoformat(date_str)
        if date < now:
            continue  # Skip past games
        teams = [t["team"]["displayName"] for t in comp.get("competitors", [])]
        league = comp.get("tournament", {}).get("name", "")
        if league in TOP_TOURNAMENTS or any(t in TOP_CLUBS for t in teams):
            future_games.append((date, parse_event(event)))
    future_games.sort(key=lambda x: x[0])
    return [g[1] for g in future_games[:3]]

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
    result = {}

    # Seahawks, Mariners, Kraken
    result["seahawks"] = get_team_game("sea", include_record=True)
    result["mariners"] = get_team_game("sea", include_record=True)
    result["kraken"] = get_team_game("sea", include_record=True)

    # NFL, NBA, MLB, NHL top games
    for league_key, league_slug in LEAGUES.items():
        result[league_key] = get_league_game(league_slug)

    # Top soccer games
    result["soccer"] = get_soccer_games()

    # Write to root-level sports.json
    with open("sports.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()