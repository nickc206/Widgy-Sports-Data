import requests
import json
from datetime import datetime, timedelta
from pytz import timezone

PACIFIC_TZ = timezone("US/Pacific")

# URLs
TEAM_URLS = {
    "seahawks": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/sea",
    "mariners": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/sea",
    "kraken": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/sea",
}

LEAGUE_URLS = {
    "nfl": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "nba": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
    "nhl": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
    "mlb": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
    "soccer": "https://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard"
}

# Top competitions and clubs
top_competitions = [
    "UEFA Champions League", "FIFA World Cup", "UEFA Euro",
    "UEFA Europa League", "UEFA Super Cup", "FIFA Club World Cup"
]

top_clubs = {
    "EPL": ["Manchester City", "Liverpool", "Arsenal", "Chelsea", "Manchester United", "Tottenham Hotspur"],
    "La Liga": ["Real Madrid", "Barcelona", "Atlético Madrid", "Sevilla"],
    "Bundesliga": ["Bayern Munich", "Borussia Dortmund", "RB Leipzig"],
    "Serie A": ["Juventus", "Inter Milan", "AC Milan", "Napoli", "Roma"],
    "Ligue 1": ["Paris Saint-Germain", "Marseille", "Monaco", "Lyon"]
}
flat_top_clubs = {club for league in top_clubs.values() for club in league}

def get_game_info(event):
    try:
        competitions = event.get("competitions", [{}])
        competition = competitions[0]
        competitors = competition.get("competitors", [])
        home = next((t for t in competitors if t.get("homeAway") == "home"), {})
        away = next((t for t in competitors if t.get("homeAway") == "away"), {})

        date_str = event.get("date", "")
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(PACIFIC_TZ)
        date_fmt = dt.strftime("%m/%d")
        time_fmt = dt.strftime("%-I:%M %p")

        return {
            "home_team": home.get("team", {}).get("displayName", ""),
            "away_team": away.get("team", {}).get("displayName", ""),
            "home_short": home.get("team", {}).get("shortDisplayName", ""),
            "away_short": away.get("team", {}).get("shortDisplayName", ""),
            "home_score": home.get("score", ""),
            "away_score": away.get("score", ""),
            "home_logo": home.get("team", {}).get("logo", ""),
            "away_logo": away.get("team", {}).get("logo", ""),
            "home_record": home.get("records", [{}])[0].get("summary", ""),
            "away_record": away.get("records", [{}])[0].get("summary", ""),
            "date": date_fmt,
            "time": time_fmt,
            "status": event.get("status", {}).get("type", {}).get("description", ""),
            "is_live": event.get("status", {}).get("type", {}).get("state", "") == "in",
            "time_left": event.get("status", {}).get("displayClock", ""),
            "quarter": event.get("status", {}).get("period", "")
        }
    except Exception:
        return blank_game()

def blank_game():
    return {
        "home_team": "", "away_team": "",
        "home_short": "", "away_short": "",
        "home_score": "", "away_score": "",
        "home_logo": "", "away_logo": "",
        "home_record": "", "away_record": "",
        "date": "", "time": "", "status": "scheduled",
        "is_live": False, "time_left": "", "quarter": ""
    }

def get_team_game(team_abbr, include_record=False):
    url = TEAM_URLS[team_abbr]
    try:
        resp = requests.get(url).json()
        next_event = resp.get("team", {}).get("nextEvent", [])
        if not next_event:
            return blank_game()
        return get_game_info(next_event[0])
    except Exception:
        return blank_game()

def get_league_game(league_key):
    url = LEAGUE_URLS[league_key]
    try:
        resp = requests.get(url).json()
        events = resp.get("events", [])
        if not events:
            return blank_game()
        return get_game_info(events[0])
    except Exception:
        return blank_game()

def score_soccer_game(event):
    score = 0
    league_name = event.get("league", {}).get("name", "")
    competition_name = event.get("name", "")
    date_str = event.get("date", "")
    try:
        game_time = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if game_time < datetime.now(tz=game_time.tzinfo):
            return -1  # discard past games
    except Exception:
        return -1

    competitors = event.get("competitions", [{}])[0].get("competitors", [])
    teams = [c.get("team", {}).get("displayName", "") for c in competitors]

    if any(t in flat_top_clubs for t in teams):
        score += 20 * sum(1 for t in teams if t in flat_top_clubs)
    if competition_name in top_competitions:
        score += 100
    elif league_name in top_competitions:
        score += 100
    elif league_name in top_clubs:
        score += 60

    days_ahead = (game_time - datetime.now(tz=game_time.tzinfo)).days
    score -= days_ahead * 0.1  # slightly prefer sooner games
    return score

def get_top_soccer_games():
    try:
        resp = requests.get(LEAGUE_URLS["soccer"]).json()
        events = resp.get("events", [])
        future_games = [e for e in events if score_soccer_game(e) >= 0]
        future_games.sort(key=lambda x: -score_soccer_game(x))
        return [get_game_info(e) for e in future_games[:3]]
    except Exception:
        return []

def main():
    data = {
        "seahawks": get_team_game("seahawks"),
        "mariners": get_team_game("mariners"),
        "kraken": get_team_game("kraken"),
        "nfl": get_league_game("nfl"),
        "nba": get_league_game("nba"),
        "nhl": get_league_game("nhl"),
        "mlb": get_league_game("mlb"),
        "soccer": get_top_soccer_games()
    }

    with open("sports.json", "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()