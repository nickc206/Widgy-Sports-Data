import json
import requests
from datetime import datetime, timedelta

OUTPUT_FILE = "sports.json"

def current_pst_time():
    utc_now = datetime.utcnow()
    pst_now = utc_now - timedelta(hours=7)
    return pst_now

def format_pst_time(dt_str):
    if not dt_str:
        return ""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    pst = dt - timedelta(hours=7)
    return pst.strftime("%I:%M %p").lstrip("0")

def format_pst_date(dt_str):
    if not dt_str:
        return ""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    pst = dt - timedelta(hours=7)
    return pst.strftime("%m/%d")

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
        "Bologna": "Bologna",
        "Atlético Madrid": "Atlético",
        "Napoli": "Napoli",
        "Marseille": "Marseille",
        "Inter Milan": "Inter",
        "AC Milan": "AC Milan",
        "AS Roma": "Roma",
        "Sevilla": "Sevilla",
        "RB Leipzig": "RB Leipzig",
        "Leverkusen": "Leverkusen",
        "Lyon": "Lyon",
        "Monaco": "Monaco",
        "Tottenham Hotspur": "Spurs",
        "Chelsea": "Chelsea"
    }.get(name, name)

TOP_TEAMS = [
    "Real Madrid", "Barcelona", "PSG", "Manchester City", "Manchester United",
    "Juventus", "Bayern Munich", "Borussia Dortmund", "Arsenal", "Liverpool", "Bologna",
    "Atlético Madrid", "Napoli", "Marseille", "Inter Milan", "AC Milan",
    "AS Roma", "Sevilla", "RB Leipzig", "Leverkusen", "Lyon", "Monaco",
    "Tottenham Hotspur", "Chelsea"
]

TOP_COMPETITIONS = [
    "UEFA Champions League", "UEFA Europa League", "FIFA World Cup", "UEFA Euro"
]

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"

# Updated to include league and team abbreviation
TEAMS = {
    "seahawks": ("football/nfl", "sea"),
    "mariners": ("baseball/mlb", "sea"),
    "kraken": ("hockey/nhl", "sea")
}

LEAGUES = {
    "nfl": "football/nfl",
    "nba": "basketball/nba",
    "nhl": "hockey/nhl",
    "mlb": "baseball/mlb"
}

SOCCER_LEAGUES = [
    "uefa.champions", "uefa.europa", "fifa.world", "uefa.euro",
    "eng.1", "esp.1", "ita.1", "ger.1", "fra.1"
]

def get_team_game(league_path, team_abbr, include_record=False):
    url = f"{BASE_URL}/{league_path}/teams/{team_abbr}"
    if include_record:
        url += "?enable=record"
    resp = requests.get(url)
    team = resp.json().get("team", {})
    next_events = team.get("nextEvent", [])
    return next_events[0] if next_events else {}

def extract_game_fields(game, show_team_record=False):
    start_time = (
        game.get("start_time") or
        game.get("date") or
        game.get("startDate") or
        ""
    )
    date = format_pst_time(start_time)
    date_raw = format_pst_date(start_time)

    status = game.get("status", {}).get("type", {}).get("description", "scheduled")
    short_status = game.get("status", {}).get("type", {}).get("shortDetail", "")
    is_live = game.get("status", {}).get("type", {}).get("state", "") == "in"
    time_left = game.get("status", {}).get("displayClock", "")
    period = game.get("status", {}).get("period", "")

    competitors = game.get("competitions", [{}])[0].get("competitors", [])
    home = competitors[0] if len(competitors) > 0 else {}
    away = competitors[1] if len(competitors) > 1 else {}

    home_team = home.get("team", {}).get("displayName", "")
    away_team = away.get("team", {}).get("displayName", "")
    home_short = team_short(home_team)
    away_short = team_short(away_team)
    home_score = home.get("score", "")
    away_score = away.get("score", "")
    home_logo = home.get("team", {}).get("logo", "")
    away_logo = away.get("team", {}).get("logo", "")
    home_record = home.get("records", [{}])[0].get("summary", "") if show_team_record else ""
    away_record = away.get("records", [{}])[0].get("summary", "") if show_team_record else ""

    return {
        "home_team": home_team,
        "away_team": away_team,
        "home_short": home_short,
        "away_short": away_short,
        "home_score": home_score,
        "away_score": away_score,
        "home_logo": home_logo,
        "away_logo": away_logo,
        "home_record": home_record,
        "away_record": away_record,
        "date": date_raw,
        "time": date,
        "status": status,
        "is_live": is_live,
        "time_left": time_left,
        "quarter": period
    }

def get_top_soccer_games():
    games = []
    for league in SOCCER_LEAGUES:
        url = f"{BASE_URL}/soccer/{league}/scoreboard"
        try:
            resp = requests.get(url).json()
            events = resp.get("events", [])
            for game in events:
                league_name = game.get("league", {}).get("name", "")
                league_rank = TOP_COMPETITIONS.index(league_name) if league_name in TOP_COMPETITIONS else 99
                game_text = json.dumps(game).lower()
                importance = 0 if league_rank < 99 else 1 if any(t.lower() in game_text for t in TOP_TEAMS) else 2
                games.append((importance, league_rank, game))
        except Exception:
            continue
    games.sort(key=lambda x: (x[0], x[1]))
    return [extract_game_fields(g[2]) for g in games[:3]]

def main():
    data = {}

    for key, (league_path, abbr) in TEAMS.items():
        game = get_team_game(league_path, abbr, include_record=True)
        data[key] = extract_game_fields(game, show_team_record=True)

    for league, endpoint in LEAGUES.items():
        url = f"{BASE_URL}/{endpoint}/scoreboard"
        try:
            resp = requests.get(url).json()
            events = resp.get("events", [])
            if events:
                data[league] = extract_game_fields(events[0])
        except Exception:
            data[league] = {}

    data["soccer"] = get_top_soccer_games()

    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()