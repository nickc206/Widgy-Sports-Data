import requests
import datetime
import json

TEAMS = {
    "seahawks": "sea",
    "mariners": "sea",
    "kraken": "sea"
}

LEAGUES = {
    "nfl": "football/nfl",
    "nba": "basketball/nba",
    "mlb": "baseball/mlb",
    "nhl": "hockey/nhl"
}

TOP_SOCCER_TEAMS = {
    "Real Madrid", "Barcelona", "Atlético Madrid",
    "Manchester City", "Manchester United", "Liverpool", "Arsenal", "Tottenham Hotspur", "Chelsea",
    "Bayern Munich", "Borussia Dortmund", "RB Leipzig",
    "Juventus", "Inter Milan", "AC Milan", "Napoli", "Roma",
    "Paris Saint-Germain", "Marseille", "Monaco",
    "Bologna"
}

SOCCER_TOURNAMENTS_PRIORITY = [
    "uefa.champions", "uefa.europa", "fifa.world", "uefa.euro", "fifa.cwc"
]

SOCCER_FALLBACK_LEAGUES = [
    "eng.1", "esp.1", "ita.1", "deu.1", "fra.1"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_json(url):
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def format_time(date_str):
    dt = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    pacific = dt.astimezone(datetime.timezone(datetime.timedelta(hours=-7)))
    return pacific.strftime("%I:%M %p").lstrip("0")

def format_date(date_str):
    dt = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    pacific = dt.astimezone(datetime.timezone(datetime.timedelta(hours=-7)))
    return pacific.strftime("%m/%d")

def get_team_game(team_abbr):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_abbr}"
    team = fetch_json(url).get("team", {})
    events = team.get("nextEvent", [])
    if not events:
        return empty_game()
    event = events[0]
    comp = event.get("competitions", [{}])[0]
    home = comp.get("competitors", [{}])[0]
    away = comp.get("competitors", [{}])[1]
    return build_game_object(event, home, away)

def get_league_game(slug):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{slug}/scoreboard"
    data = fetch_json(url)
    events = data.get("events", [])
    if not events:
        return empty_game()
    event = events[0]
    comp = event.get("competitions", [{}])[0]
    home = comp.get("competitors", [{}])[0]
    away = comp.get("competitors", [{}])[1]
    return build_game_object(event, home, away)

def build_game_object(event, home, away):
    status = event.get("status", {}).get("type", {}).get("description", "scheduled").lower()
    is_live = status == "in progress"
    return {
        "home_team": home.get("team", {}).get("displayName", ""),
        "away_team": away.get("team", {}).get("displayName", ""),
        "home_short": home.get("team", {}).get("shortDisplayName", ""),
        "away_short": away.get("team", {}).get("shortDisplayName", ""),
        "home_score": home.get("score", ""),
        "away_score": away.get("score", ""),
        "home_logo": home.get("team", {}).get("logos", [{}])[0].get("href", ""),
        "away_logo": away.get("team", {}).get("logos", [{}])[0].get("href", ""),
        "home_record": home.get("records", [{}])[0].get("summary", ""),
        "away_record": away.get("records", [{}])[0].get("summary", ""),
        "date": format_date(event.get("date", "")),
        "time": format_time(event.get("date", "")),
        "status": status,
        "is_live": is_live,
        "time_left": event.get("status", {}).get("displayClock", ""),
        "quarter": event.get("status", {}).get("period", "")
    }

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

def get_top_soccer_games():
    games = []
    now = datetime.datetime.utcnow()

    for league in SOCCER_TOURNAMENTS_PRIORITY + SOCCER_FALLBACK_LEAGUES:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"
        try:
            data = fetch_json(url)
        except Exception:
            continue
        for event in data.get("events", []):
            try:
                comp = event.get("competitions", [{}])[0]
                home = comp.get("competitors", [{}])[0]
                away = comp.get("competitors", [{}])[1]
                home_name = home.get("team", {}).get("displayName", "")
                away_name = away.get("team", {}).get("displayName", "")
                start = datetime.datetime.fromisoformat(event.get("date", "").replace("Z", "+00:00"))
                if start < now:
                    continue
                if league in SOCCER_TOURNAMENTS_PRIORITY or home_name in TOP_SOCCER_TEAMS or away_name in TOP_SOCCER_TEAMS:
                    games.append((start, build_game_object(event, home, away)))
            except Exception:
                continue

    games.sort(key=lambda x: x[0])
    return [g[1] for g in games[:3]]

def main():
    result = {}

    for key, abbr in TEAMS.items():
        try:
            result[key] = get_team_game(abbr)
        except Exception:
            result[key] = empty_game()

    for league_key, league_slug in LEAGUES.items():
        try:
            result[league_key] = get_league_game(league_slug)
        except Exception:
            result[league_key] = empty_game()

    result["soccer"] = get_top_soccer_games()

    with open("sports.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()