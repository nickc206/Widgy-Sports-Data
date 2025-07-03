import json
import requests
from datetime import datetime, timedelta
import pytz

# Constants
PST = pytz.timezone('US/Pacific')
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Top clubs fallback for soccer
TOP_CLUBS = ["Real Madrid", "Barcelona", "Manchester City", "PSG", "Juventus", "Bayern Munich", "Liverpool", "Arsenal", "Inter Milan", "AC Milan", "Bologna"]

# Helper to format date/time
def format_pst_time(iso_str):
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    pst_dt = dt.astimezone(PST)
    return pst_dt.strftime("%m/%d"), pst_dt.strftime("%I:%M %p").lstrip("0")

def extract_game_fields(game, include_record=False):
    date, time = format_pst_time(game['start_time'])
    return {
        "home_team": game['home_team'],
        "away_team": game['away_team'],
        "home_score": game.get("home_score", ""),
        "away_score": game.get("away_score", ""),
        "short_home": game.get("short_home", ""),
        "short_away": game.get("short_away", ""),
        "start_date": date,
        "start_time": time,
        "iso_start_time": game["start_time"],
        "status": game["status"],  # scheduled, live, final
        "league": game.get("league", ""),
        "is_live": game.get("is_live", False),
        "time_left": game.get("time_left", ""),
        "quarter": game.get("quarter", ""),
        "home_record": game.get("home_record", "") if include_record else "",
        "away_record": game.get("away_record", "") if include_record else ""
    }

def get_team_game(team_name):
    # Placeholder API call — replace with your real ESPN team-specific endpoint
    # Use team_name to dynamically choose which endpoint
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_name}/schedule"
    resp = requests.get(url, headers=HEADERS).json()
    for event in resp.get("events", []):
        # Custom parsing here for ESPN’s team page
        # Placeholder logic
        pass
    return {}

def get_league_top_game(sport):
    # Placeholder URL for league — MLB, NBA, etc.
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/scoreboard"
    resp = requests.get(url, headers=HEADERS).json()
    games = resp.get("events", [])
    if not games:
        return {}
    # Apply prioritization if multiple games
    # Placeholder logic: pick the first
    game = games[0]
    return extract_game_fields({
        "home_team": game["competitions"][0]["competitors"][0]["team"]["displayName"],
        "away_team": game["competitions"][0]["competitors"][1]["team"]["displayName"],
        "start_time": game["date"],
        "status": game["status"]["type"]["name"].lower(),
        "league": resp["leagues"][0]["abbreviation"]
    }, include_record=True)

def get_top_soccer_games():
    # Multiple league endpoints or one scoreboard page (e.g., soccer/scoreboard)
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard"
    resp = requests.get(url, headers=HEADERS).json()
    events = resp.get("events", [])
    ranked_games = []

    for game in events:
        league = game["league"]["name"]
        home = game["competitions"][0]["competitors"][0]["team"]["displayName"]
        away = game["competitions"][0]["competitors"][1]["team"]["displayName"]
        importance = 0
        if any(t in home + away for t in TOP_CLUBS):
            importance += 2
        if "Champions League" in league:
            importance += 5
        elif "World Cup" in league or "UEFA Euro" in league:
            importance += 5
        elif "Premier League" in league:
            importance += 1
        ranked_games.append((importance, {
            "home_team": home,
            "away_team": away,
            "start_time": game["date"],
            "status": game["status"]["type"]["name"].lower(),
            "league": league
        }))
    
    # Sort by importance and time
    top_games = sorted(ranked_games, key=lambda x: (-x[0], x[1]["start_time"]))
    return [extract_game_fields(g[1], include_record=True) for g in top_games[:3]]

def main():
    data = {}

    # Seahawks
    data["seahawks"] = extract_game_fields(get_team_game("sea"), include_record=True)
    data["seahawks"]["home_or_away"] = "vs" if data["seahawks"]["home_team"] == "Seattle Seahawks" else "@"

    # Kraken
    data["kraken"] = extract_game_fields(get_team_game("sea"), include_record=True)
    data["kraken"]["home_or_away"] = "vs" if data["kraken"]["home_team"] == "Seattle Kraken" else "@"

    # Mariners
    data["mariners"] = extract_game_fields(get_team_game("sea"), include_record=True)
    data["mariners"]["home_or_away"] = "vs" if data["mariners"]["home_team"] == "Seattle Mariners" else "@"

    # League top games
    data["nfl"] = get_league_top_game("football/nfl")
    data["nba"] = get_league_top_game("basketball/nba")
    data["mlb"] = get_league_top_game("baseball/mlb")
    data["nhl"] = get_league_top_game("hockey/nhl")

    # Top 3 soccer
    data["soccer"] = get_top_soccer_games()

    # Save to file
    with open("sports.json", "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()
