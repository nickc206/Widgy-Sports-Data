import json
import requests
from datetime import datetime, timedelta

OUTPUT_FILE = "sports.json"

# Pacific Time (adjust manually if daylight saving changes)
def current_pst_time():
    return datetime.utcnow() - timedelta(hours=7)

def format_pst_time(dt_str):
    if not dt_str:
        return ""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    pst = dt - timedelta(hours=7)
    return pst.strftime("%-I:%M %p")

def format_pst_date(dt_str):
    if not dt_str:
        return ""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    pst = dt - timedelta(hours=7)
    return pst.strftime("%m/%d")

# League and team short names
def league_short(name):
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
    }.get(name, name)

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
        "Tottenham Hotspur": "Spurs",
        "Atlético Madrid": "Atlético",
        "Marseille": "Marseille",
        "Napoli": "Napoli",
        "Bologna": "Bologna"
    }.get(name, name)

TOP_TEAMS = [
    "Real Madrid", "Barcelona", "PSG", "Manchester City", "Manchester United",
    "Juventus", "Bayern Munich", "Borussia Dortmund", "Arsenal", "Liverpool",
    "Tottenham Hotspur", "Atlético Madrid", "Marseille", "Napoli", "Bologna"
]

TOP_COMPETITIONS = [
    "UEFA Champions League", "UEFA Europa League", "FIFA World Cup", "UEFA Euro"
]

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"

SOCCER_LEAGUES = [
    "uefa.champions", "uefa.europa", "fifa.world", "uefa.euro",
    "eng.1", "esp.1", "ita.1", "ger.1", "fra.1"
]

LEAGUES = {
    "nfl": "football/nfl",
    "nba": "basketball/nba",
    "nhl": "hockey/nhl",
    "mlb": "baseball/mlb"
}

TEAM_ENDPOINTS = {
    "seahawks": "football/nfl/teams/sea",
    "mariners": "baseball/mlb/teams/sea",
    "kraken": "hockey/nhl/teams/sea"
}

def extract_game_fields(game, show_record=False):
    try:
        start = game.get("date")
        status = game.get("status", {}).get("type", {})
        competition = game.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])
        if len(competitors) < 2:
            competitors = [{}, {}]

        home = [c for c in competitors if c.get("homeAway") == "home"]
        away = [c for c in competitors if c.get("homeAway") == "away"]
        home = home[0] if home else {}
        away = away[0] if away else {}

        return {
            "home_team": home.get("team", {}).get("displayName", ""),
            "away_team": away.get("team", {}).get("displayName", ""),
            "home_short": team_short(home.get("team", {}).get("displayName", "")),
            "away_short": team_short(away.get("team", {}).get("displayName", "")),
            "home_score": home.get("score", ""),
            "away_score": away.get("score", ""),
            "home_logo": home.get("team", {}).get("logo", ""),
            "away_logo": away.get("team", {}).get("logo", ""),
            "home_record": home.get("records", [{}])[0].get("summary", "") if show_record else "",
            "away_record": away.get("records", [{}])[0].get("summary", "") if show_record else "",
            "date": format_pst_date(start),
            "time": format_pst_time(start),
            "status": status.get("description", "scheduled"),
            "is_live": status.get("state") == "in",
            "time_left": game.get("status", {}).get("displayClock", ""),
            "quarter": game.get("status", {}).get("period", "")
        }
    except Exception:
        return {
            "home_team": "", "away_team": "", "home_short": "", "away_short": "",
            "home_score": "", "away_score": "", "home_logo": "", "away_logo": "",
            "home_record": "", "away_record": "", "date": "", "time": "",
            "status": "scheduled", "is_live": False, "time_left": "", "quarter": ""
        }

def get_team_game(endpoint):
    try:
        url = f"{BASE_URL}/{endpoint}?enable=team.schedule"
        resp = requests.get(url).json()
        team = resp.get("team", {})
        events = team.get("nextEvent") or team.get("events") or []
        return events[0] if events else {}
    except Exception:
        return {}

def get_top_soccer_games():
    future_games = []
    now = current_pst_time()

    for league in SOCCER_LEAGUES:
        url = f"{BASE_URL}/soccer/{league}/scoreboard"
        try:
            resp = requests.get(url).json()
            for game in resp.get("events", []):
                dt_str = game.get("date")
                if not dt_str:
                    continue
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00")) - timedelta(hours=7)
                    if dt < now:
                        continue
                except Exception:
                    continue

                league_name = game.get("league", {}).get("name", "")
                league_rank = TOP_COMPETITIONS.index(league_name) if league_name in TOP_COMPETITIONS else 99
                importance = 0 if league_rank < 99 else 1 if any(t.lower() in str(game).lower() for t in TOP_TEAMS) else 2
                future_games.append((importance, league_rank, dt_str, game))
        except Exception:
            continue

    future_games.sort()
    return [extract_game_fields(g[3]) for g in future_games[:3]]

def get_league_top_game(endpoint):
    try:
        url = f"{BASE_URL}/{endpoint}/scoreboard"
        resp = requests.get(url).json()
        return extract_game_fields(resp.get("events", [])[0]) if resp.get("events") else extract_game_fields({})
    except Exception:
        return extract_game_fields({})

def main():
    data = {}

    for key, endpoint in TEAM_ENDPOINTS.items():
        game = get_team_game(endpoint)
        data[key] = extract_game_fields(game, show_record=True)

    for league, endpoint in LEAGUES.items():
        data[league] = get_league_top_game(endpoint)

    data["soccer"] = get_top_soccer_games()

    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()