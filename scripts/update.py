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
    return pst.strftime("%I:%M %p")

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
        "Atletico Madrid": "Atlético",
        "Marseille": "Marseille",
        "Napoli": "Napoli",
        "Inter Milan": "Inter",
        "AC Milan": "AC Milan",
        "Chelsea": "Chelsea",
        "Tottenham Hotspur": "Spurs",
        "Ajax": "Ajax",
        "Porto": "Porto",
        "Benfica": "Benfica",
        "Roma": "Roma"
    }.get(name, name)

TOP_TEAMS = [
    "Real Madrid", "Barcelona", "PSG", "Manchester City", "Manchester United",
    "Juventus", "Bayern Munich", "Borussia Dortmund", "Arsenal", "Liverpool",
    "Bologna", "Atletico Madrid", "Marseille", "Napoli", "Inter Milan",
    "AC Milan", "Chelsea", "Tottenham Hotspur", "Ajax", "Porto", "Benfica", "Roma"
]

TOP_COMPETITIONS = [
    "UEFA Champions League", "FIFA World Cup", "UEFA Euro", "UEFA Europa League"
]

SOCCER_LEAGUES = [
    "uefa.champions", "uefa.europa", "fifa.world", "uefa.euro",
    "eng.1", "esp.1", "ita.1", "ger.1", "fra.1"
]

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

def get_team_game(sport_path, team_abbr, include_record=False):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_abbr}"
    if include_record:
        url += "?enable=record"
    try:
        resp = requests.get(url)
        team = resp.json().get("team", {})
        return team.get("nextEvent", [{}])[0]
    except Exception:
        return {}

def extract_game_fields(game, show_team_record=False):
    start_time = game.get("date") or game.get("start_date") or game.get("startTime")
    if not start_time:
        return {}

    status_info = game.get("status", {})
    competition = game.get("competitions", [{}])[0]
    competitors = competition.get("competitors", [])

    if len(competitors) < 2:
        return {}

    home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
    away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

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
        "status": status_info.get("type", {}).get("description", "scheduled"),
        "is_live": status_info.get("type", {}).get("state", "") == "in",
        "time_left": status_info.get("displayClock", ""),
        "quarter": status_info.get("period", "")
    }

def get_top_soccer_games():
    games = []
    for league in SOCCER_LEAGUES:
        try:
            resp = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard").json()
            for game in resp.get("events", []):
                league_name = game.get("league", {}).get("name", "")
                league_rank = TOP_COMPETITIONS.index(league_name) if league_name in TOP_COMPETITIONS else 99
                importance = (
                    0 if league_rank < 99 else
                    1 if any(team.lower() in json.dumps(game).lower() for team in TOP_TEAMS)
                    else 2
                )
                games.append((importance, league_rank, game))
        except Exception:
            continue
    games.sort()
    return [extract_game_fields(g[2]) for g in games[:3] if extract_game_fields(g[2])]

def main():
    data = {}

    for label, (sport_path, abbr) in TEAMS.items():
        game = get_team_game(sport_path, abbr, include_record=True)
        fields = extract_game_fields(game, show_team_record=True)
        if fields:
            data[label] = fields

    for label, sport_path in LEAGUES.items():
        try:
            resp = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard").json()
            events = resp.get("events", [])
            if events:
                game = events[0]
                fields = extract_game_fields(game)
                if fields:
                    data[label] = fields
        except Exception:
            continue

    data["soccer"] = get_top_soccer_games()

    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()