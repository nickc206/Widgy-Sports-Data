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
        "Bologna": "Bologna",
        "Atlético Madrid": "Atlético",
        "Napoli": "Napoli",
        "Inter Milan": "Inter",
        "AC Milan": "AC Milan",
        "Marseille": "Marseille",
        "AS Roma": "Roma",
        "Chelsea": "Chelsea",
        "Tottenham Hotspur": "Spurs",
        "Newcastle United": "Newcastle",
        "RB Leipzig": "RB Leipzig"
    }.get(name, name)

TOP_TEAMS = [
    "Real Madrid", "Barcelona", "PSG", "Manchester City", "Manchester United",
    "Juventus", "Bayern Munich", "Borussia Dortmund", "Arsenal", "Liverpool",
    "Bologna", "Atlético Madrid", "Napoli", "Inter Milan", "AC Milan", "Marseille",
    "AS Roma", "Chelsea", "Tottenham Hotspur", "Newcastle United", "RB Leipzig"
]

TOP_COMPETITIONS = [
    "UEFA Champions League", "FIFA World Cup", "UEFA Euro", "UEFA Europa League"
]

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"

TEAMS = {
    "seahawks": "football/nfl/teams/sea",
    "mariners": "baseball/mlb/teams/sea",
    "kraken": "hockey/nhl/teams/sea"
}

LEAGUES = {
    "nfl": "football/nfl",
    "nba": "basketball/nba",
    "nhl": "hockey/nhl",
    "mlb": "baseball/mlb",
}

SOCCER_LEAGUES = [
    "uefa.champions", "uefa.europa", "fifa.world", "uefa.euro",
    "eng.1", "esp.1", "ita.1", "ger.1", "fra.1"
]

def extract_game_fields(game, show_team_record=False):
    date = format_pst_time(game.get('date'))
    date_raw = format_pst_date(game.get('date'))
    status = game.get("status", {}).get("type", {}).get("description", "scheduled")
    short_status = game.get("status", {}).get("type", {}).get("shortDetail", "")
    is_live = game.get("status", {}).get("type", {}).get("state", "") == "in"
    time_left = game.get("status", {}).get("displayClock", "")
    period = game.get("status", {}).get("period", "")

    competitors = game.get("competitions", [{}])[0].get("competitors", [])
    home, away = sorted(competitors, key=lambda x: x.get("homeAway") != "home")

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

def get_team_game(team_url):
    resp = requests.get(f"{BASE_URL}/{team_url}")
    return resp.json().get("team", {}).get("nextEvent", [{}])[0]

def get_top_soccer_games():
    games = []
    for league in SOCCER_LEAGUES:
        try:
            resp = requests.get(f"{BASE_URL}/soccer/{league}/scoreboard")
            for game in resp.json().get("events", []):
                league_name = game.get("league", {}).get("name", "")
                league_rank = TOP_COMPETITIONS.index(league_name) if league_name in TOP_COMPETITIONS else 99
                importance = (
                    0 if league_rank < 99 else
                    1 if any(team.lower() in str(game).lower() for team in TOP_TEAMS) else
                    2
                )
                games.append((importance, league_rank, game))
        except:
            continue
    games.sort()
    return [extract_game_fields(g[2]) for g in games[:3]]

def main():
    data = {}

    # Get selected teams
    for key, url in TEAMS.items():
        try:
            game = get_team_game(url)
            data[key] = extract_game_fields(game, show_team_record=True)
        except:
            data[key] = {}

    # Top game per league
    for league, endpoint in LEAGUES.items():
        try:
            resp = requests.get(f"{BASE_URL}/{endpoint}/scoreboard")
            events = resp.json().get("events", [])
            if events:
                data[league] = extract_game_fields(events[0])
            else:
                data[league] = {}
        except:
            data[league] = {}

    # Top 3 soccer games
    data["soccer"] = get_top_soccer_games()

    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()
