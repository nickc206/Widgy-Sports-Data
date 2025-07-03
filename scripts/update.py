import json
import requests
from datetime import datetime, timedelta

OUTPUT_FILE = "sports.json"

# Return current time in PST
def current_pst_time():
    utc_now = datetime.utcnow()
    pst_now = utc_now - timedelta(hours=7)  # adjust if daylight saving changes
    return pst_now

# Format PST time string from UTC time
def format_pst_time(dt_str):
    if not dt_str:
        return ""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    pst = dt - timedelta(hours=7)
    return pst.strftime("%I:%M %p")

# Format PST date string from UTC time
def format_pst_date(dt_str):
    if not dt_str:
        return ""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    pst = dt - timedelta(hours=7)
    return pst.strftime("%m/%d")

# Get league short name
def league_short(league):
    return {
        "English Premier League": "EPL",
        "Spanish La Liga": "La Liga",
        "German Bundesliga": "Bundesliga",
        "Italian Serie A": "Serie A",
        "French Ligue 1": "Ligue 1",
        "UEFA Champions League": "Champions League",
        "UEFA Europa League": "Europa League",
        "FIFA World Cup": "World Cup",
        "UEFA Euro": "Euro"
    }.get(league, league)

# Get team short name
def team_short(name):
    return {
        "Paris Saint-Germain": "PSG",
        "Manchester City": "Man City",
        "Manchester United": "Man Utd",
        "Real Madrid": "Real Madrid",
        "Barcelona": "Barcelona",
        "Juventus": "Juventus",
        "Bayern Munich": "Bayern",
        "Borussia Dortmund": "Dortmund",
        "Liverpool": "Liverpool",
        "Arsenal": "Arsenal",
        "Bologna": "Bologna"
    }.get(name, name)

# Top teams for fallback logic
TOP_TEAMS = [
    "Real Madrid", "Barcelona", "PSG", "Manchester City", "Manchester United",
    "Juventus", "Bayern Munich", "Borussia Dortmund", "Arsenal", "Liverpool", "Bologna"
]

# List of important competitions
TOP_COMPETITIONS = [
    "UEFA Champions League", "UEFA Europa League", "FIFA World Cup", "UEFA Euro"
]

# API base URL
BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"

# Selected teams by sport (correct endpoints)
SELECTED_TEAMS = {
    "seahawks": ("football/nfl", "sea"),
    "mariners": ("baseball/mlb", "sea"),
    "kraken": ("hockey/nhl", "sea")
}

# Top leagues by sport
LEAGUES = {
    "nfl": "football/nfl",
    "nba": "basketball/nba",
    "mlb": "baseball/mlb",
    "nhl": "hockey/nhl",
}

# Soccer league IDs to check
SOCCER_LEAGUES = [
    "uefa.champions", "uefa.europa", "fifa.world", "uefa.euro",
    "eng.1", "esp.1", "ita.1", "ger.1", "fra.1"
]

def get_team_game(sport_path, team_abbr):
    url = f"{BASE_URL}/{sport_path}/teams/{team_abbr}"
    try:
        resp = requests.get(url).json()
        team = resp.get("team", {})
        return team.get("nextEvent", [{}])[0]
    except Exception:
        return {}

def extract_game_fields(game, show_team_record=False):
    if not game:
        return {}
    competitions = game.get("competitions", [{}])[0]
    competitors = competitions.get("competitors", [{}])

    if len(competitors) < 2:
        return {}

    home = competitors[0] if competitors[0].get("homeAway") == "home" else competitors[1]
    away = competitors[1] if home == competitors[0] else competitors[0]

    status = game.get("status", {}).get("type", {})
    start_time = game.get("date", "")

    return {
        "home_team": home.get("team", {}).get("displayName", ""),
        "away_team": away.get("team", {}).get("displayName", ""),
        "home_short": team_short(home.get("team", {}).get("displayName", "")),
        "away_short": team_short(away.get("team", {}).get("displayName", "")),
        "home_score": home.get("score", ""),
        "away_score": away.get("score", ""),
        "home_logo": home.get("team", {}).get("logo", ""),
        "away_logo": away.get("team", {}).get("logo", ""),
        "home_record": home.get("records", [{}])[0].get("summary", "") if show_team_record else "",
        "away_record": away.get("records", [{}])[0].get("summary", "") if show_team_record else "",
        "date": format_pst_date(start_time),
        "time": format_pst_time(start_time),
        "status": status.get("description", "scheduled"),
        "is_live": status.get("state") == "in",
        "time_left": game.get("status", {}).get("displayClock", ""),
        "quarter": game.get("status", {}).get("period", "")
    }

def get_top_soccer_games():
    games = []
    for league in SOCCER_LEAGUES:
        try:
            url = f"{BASE_URL}/soccer/{league}/scoreboard"
            resp = requests.get(url).json()
            events = resp.get("events", [])
            for event in events:
                league_name = event.get("league", {}).get("name", "")
                league_rank = TOP_COMPETITIONS.index(league_name) if league_name in TOP_COMPETITIONS else 99
                importance = 0 if league_rank < 99 else 1 if any(team.lower() in str(event).lower() for team in TOP_TEAMS) else 2
                games.append((importance, league_rank, event))
        except Exception:
            continue
    games.sort()
    return [extract_game_fields(g[2]) for g in games[:3]]

def main():
    data = {}

    # Selected teams (Seahawks, Mariners, Kraken)
    for label, (sport_path, abbr) in SELECTED_TEAMS.items():
        game = get_team_game(sport_path, abbr)
        data[label] = extract_game_fields(game, show_team_record=True)

    # Top league game from NFL, NBA, MLB, NHL
    for league, path in LEAGUES.items():
        try:
            url = f"{BASE_URL}/{path}/scoreboard"
            events = requests.get(url).json().get("events", [])
            if events:
                data[league] = extract_game_fields(events[0])
        except Exception:
            data[league] = {}

    # Top 3 prioritized soccer games
    data["soccer"] = get_top_soccer_games()

    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()
