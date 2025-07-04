import requests
import json
from datetime import datetime, timedelta
import os

TEAMS = {
    "seahawks": {"sport": "football", "league": "nfl", "team_slug": "sea"},
    "mariners": {"sport": "baseball", "league": "mlb", "team_slug": "sea"},
    "kraken": {"sport": "hockey", "league": "nhl", "team_slug": "sea"},
}

LEAGUES = {
    "nfl": "football/nfl",
    "nba": "basketball/nba",
    "mlb": "baseball/mlb",
    "nhl": "hockey/nhl"
}

TOP_CLUBS = {
    "Real Madrid", "Barcelona", "Manchester City", "Manchester United", "Liverpool",
    "Arsenal", "Chelsea", "Tottenham", "Bayern Munich", "Borussia Dortmund", "RB Leipzig",
    "Juventus", "Inter Milan", "AC Milan", "Napoli", "Roma", "PSG", "Marseille",
    "Monaco", "Atletico Madrid", "Sevilla", "Valencia", "Ajax", "Porto", "Benfica", "Sporting CP", "Bologna"
}

TOP_NATIONAL_TEAMS = {
    "Spain", "Italy", "Germany", "England", "France", "Brazil", "Argentina", "Belgium", "Portugal", "Netherlands"
}

SOCCER_LEAGUES = [
    "eng.1", "esp.1", "ita.1", "ger.1", "fra.1",  # EPL, La Liga, Serie A, Bundesliga, Ligue 1
    "uefa.champions", "uefa.europa", "fifa.world", "uefa.euro", "fifa.club"  # Tournaments
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_json(url):
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def format_datetime(iso_str):
    dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    pacific = dt.astimezone().astimezone()
    return dt.strftime("%m/%d"), dt.strftime("%-I:%M %p")

def extract_game_info(event):
    competitors = event.get("competitions", [{}])[0].get("competitors", [])
    home = next((c for c in competitors if c.get("homeAway") == "home"), {})
    away = next((c for c in competitors if c.get("homeAway") == "away"), {})

    def short_name(team):
        name = team.get("team", {}).get("shortDisplayName", "")
        return name or team.get("team", {}).get("displayName", "")

    return {
        "home_team": home.get("team", {}).get("displayName", ""),
        "away_team": away.get("team", {}).get("displayName", ""),
        "home_short": short_name(home),
        "away_short": short_name(away),
        "home_score": home.get("score", ""),
        "away_score": away.get("score", ""),
        "home_logo": home.get("team", {}).get("logo", ""),
        "away_logo": away.get("team", {}).get("logo", ""),
        "home_record": home.get("records", [{}])[0].get("summary", ""),
        "away_record": away.get("records", [{}])[0].get("summary", ""),
        "date": "",
        "time": "",
        "status": event.get("status", {}).get("type", {}).get("name", "").lower(),
        "is_live": event.get("status", {}).get("type", {}).get("state", "") == "in",
        "time_left": event.get("status", {}).get("displayClock", ""),
        "quarter": event.get("status", {}).get("period", "")
    }

def get_team_game(team_info):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{team_info['sport']}/{team_info['league']}/teams/{team_info['team_slug']}"
    try:
        data = fetch_json(url)
        events = data.get("team", {}).get("nextEvent", [])
        if not events:
            return empty_game()
        event = events[0]
        game = extract_game_info(event)
        game["date"], game["time"] = format_datetime(event["date"])
        game["status"] = event.get("status", {}).get("type", {}).get("name", "").lower()
        game["is_live"] = event.get("status", {}).get("type", {}).get("state", "") == "in"
        return game
    except Exception as e:
        print(f"[ERROR] Failed to fetch team game: {team_info['team_slug']} - {e}")
        return empty_game()

def get_league_game(league_slug):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{league_slug}/scoreboard"
    try:
        data = fetch_json(url)
        events = data.get("events", [])
        if not events:
            return empty_game()
        event = events[0]
        game = extract_game_info(event)
        game["date"], game["time"] = format_datetime(event["date"])
        game["status"] = event.get("status", {}).get("type", {}).get("name", "").lower()
        game["is_live"] = event.get("status", {}).get("type", {}).get("state", "") == "in"
        return game
    except Exception as e:
        print(f"[ERROR] Failed to fetch league: {league_slug} - {e}")
        return empty_game()

def get_top_soccer_games():
    today = datetime.utcnow()
    best = []

    for league in SOCCER_LEAGUES:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"
        try:
            data = fetch_json(url)
            for event in data.get("events", []):
                if "competitions" not in event: continue
                comp = event["competitions"][0]
                teams = [t["team"]["displayName"] for t in comp.get("competitors", [])]
                logos = [t["team"].get("logo", "") for t in comp.get("competitors", [])]
                scores = [t.get("score", "") for t in comp.get("competitors", [])]

                event_dt = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
                days_until = (event_dt - today).days

                if days_until < 0 or days_until > 30:
                    continue

                importance = 0
                for team in teams:
                    if team in TOP_CLUBS or team in TOP_NATIONAL_TEAMS:
                        importance += 10
                if "world" in league or "euro" in league:
                    importance += 4
                elif "champions" in league:
                    importance += 3
                elif "europa" in league:
                    importance += 2
                elif "club" in league:
                    importance += 1

                best.append({
                    "home_team": teams[0],
                    "away_team": teams[1],
                    "home_short": teams[0],
                    "away_short": teams[1],
                    "home_score": scores[0],
                    "away_score": scores[1],
                    "home_logo": logos[0],
                    "away_logo": logos[1],
                    "home_record": "",
                    "away_record": "",
                    "date": event_dt.strftime("%