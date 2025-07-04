import requests
import json
from datetime import datetime, timedelta
import pytz

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

TEAM_IDS = {
    "seahawks": "26",
    "mariners": "12",
    "kraken": "90",
    "nfl": "nfl",
    "nba": "nba",
    "mlb": "mlb",
    "nhl": "nhl"
}

TOP_SOCCER_TEAMS = [
    "Real Madrid", "Barcelona", "Atlético Madrid",
    "Manchester City", "Manchester United", "Liverpool", "Arsenal", "Chelsea", "Tottenham Hotspur",
    "Bayern Munich", "Borussia Dortmund",
    "Juventus", "Inter Milan", "AC Milan", "Napoli",
    "Paris Saint-Germain", "Marseille", "Monaco",
    "Ajax", "Porto", "Benfica", "Sporting CP",
    "Bologna"
]

TOP_SOCCER_LEAGUES = [
    "UEFA Champions League", "FIFA World Cup", "UEFA Euro", "UEFA Europa League",
    "English Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1",
    "FIFA Club World Cup"
]

PACIFIC_TZ = pytz.timezone("America/Los_Angeles")

def get_json(url):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def format_time(iso_time):
    dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00")).astimezone(PACIFIC_TZ)
    return dt.strftime("%I:%M %p").lstrip("0"), dt.strftime("%m/%d")

def get_scoreboard(sport):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{sport}/scoreboard"
    return get_json(url)

def get_team_game(team_id, include_record=False):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}"
    data = get_json(url)
    team = data.get("team", {})
    next_event = team.get("nextEvent", [])
    if not next_event:
        return empty_game()
    event = next_event[0]
    competitors = event["competitions"][0]["competitors"]
    home = next(c for c in competitors if c["homeAway"] == "home")
    away = next(c for c in competitors if c["homeAway"] == "away")

    time_str, date_str = format_time(event["date"])
    game = {
        "home_team": home["team"]["displayName"],
        "away_team": away["team"]["displayName"],
        "home_short": home["team"].get("shortDisplayName", ""),
        "away_short": away["team"].get("shortDisplayName", ""),
        "home_score": home.get("score", ""),
        "away_score": away.get("score", ""),
        "home_logo": home["team"]["logos"][0]["href"],
        "away_logo": away["team"]["logos"][0]["href"],
        "home_record": home["records"][0]["summary"] if include_record and "records" in home else "",
        "away_record": away["records"][0]["summary"] if include_record and "records" in away else "",
        "date": date_str,
        "time": time_str,
        "status": event["status"]["type"]["description"],
        "is_live": event["status"]["type"]["state"] == "in",
        "time_left": event["status"]["displayClock"],
        "quarter": event["status"]["period"]
    }
    return game

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

def get_league_game(sport):
    games = get_scoreboard(sport).get("events", [])
    if not games:
        return empty_game()
    game = games[0]
    comp = game["competitions"][0]
    competitors = comp["competitors"]
    home = next(c for c in competitors if c["homeAway"] == "home")
    away = next(c for c in competitors if c["homeAway"] == "away")
    time_str, date_str = format_time(game["date"])
    return {
        "home_team": home["team"]["displayName"],
        "away_team": away["team"]["displayName"],
        "home_short": home["team"].get("shortDisplayName", ""),
        "away_short": away["team"].get("shortDisplayName", ""),
        "home_score": home.get("score", "0"),
        "away_score": away.get("score", "0"),
        "home_logo": home["team"]["logos"][0]["href"],
        "away_logo": away["team"]["logos"][0]["href"],
        "home_record": home.get("records", [{}])[0].get("summary", ""),
        "away_record": away.get("records", [{}])[0].get("summary", ""),
        "date": date_str,
        "time": time_str,
        "status": game["status"]["type"]["description"],
        "is_live": game["status"]["type"]["state"] == "in",
        "time_left": game["status"]["displayClock"],
        "quarter": game["status"]["period"]
    }

def get_top_soccer_games():
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard"
    data = get_json(url)
    events = data.get("events", [])
    future_games = []
    now = datetime.now(pytz.utc)

    for event in events:
        league = event.get("leagues", [{}])[0].get("name", "")
        comp = event.get("competitions", [{}])[0]
        competitors = comp.get("competitors", [])
        if len(competitors) < 2:
            continue
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})
        home_name = home.get("team", {}).get("displayName", "")
        away_name = away.get("team", {}).get("displayName", "")

        # Only include future games
        try:
            event_time = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
            if event_time < now:
                continue
        except:
            continue

        time_str, date_str = format_time(event["date"])
        score = {
            "home_team": home_name,
            "away_team": away_name,
            "home_short": home.get("team", {}).get("shortDisplayName", home_name),
            "away_short": away.get("team", {}).get("shortDisplayName", away_name),
            "home_score": home.get("score", "0"),
            "away_score": away.get("score", "0"),
            "home_logo": home.get("team", {}).get("logos", [{}])[0].get("href", ""),
            "away_logo": away.get("team", {}).get("logos", [{}])[0].get("href", ""),
            "home_record": home.get("records", [{}])[0].get("summary", ""),
            "away_record": away.get("records", [{}])[0].get("summary", ""),
            "date": date_str,
            "time": time_str,
            "status": event.get("status", {}).get("type", {}).get("description", ""),
            "is_live": event.get("status", {}).get("type", {}).get("state", "") == "in",
            "time_left": event.get("status", {}).get("displayClock", "0'"),
            "quarter": event.get("status", {}).get("period", "")
        }

        priority = 0
        if league in TOP_SOCCER_LEAGUES:
            priority += 10
        if home_name in TOP_SOCCER_TEAMS or away_name in TOP_SOCCER_TEAMS:
            priority += 5
        priority -= (event_time - now).days  # earlier = higher priority
        future_games.append((priority, score))

    top_games = sorted(future_games, key=lambda x: -x[0])[:3]
    return [game for _, game in top_games]

def main():
    data = {
        "seahawks": get_team_game("26"),
        "mariners": get_team_game("sea"),
        "kraken": get_team_game("sea"),
        "nfl": get_league_game("nfl"),
        "nba": get_league_game("nba"),
        "mlb": get_league_game("mlb"),
        "nhl": get_league_game("nhl"),
        "soccer": get_top_soccer_games()
    }

    with open("sports.json", "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()