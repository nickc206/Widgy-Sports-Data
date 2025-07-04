import requests
import json
from datetime import datetime, timedelta
import pytz

PACIFIC = pytz.timezone("US/Pacific")

TOP_SOCCER_TEAMS = {
    "Real Madrid", "Barcelona", "Manchester City", "Manchester United", "Liverpool",
    "Arsenal", "Chelsea", "Tottenham Hotspur", "PSG", "Bayern Munich", "Borussia Dortmund",
    "Juventus", "AC Milan", "Inter Milan", "Napoli", "Atlético Madrid", "Marseille",
    "Bologna", "RB Leipzig", "Leverkusen", "Roma"
}

TOP_SOCCER_LEAGUES = {
    "Champions League", "Europa League", "World Cup", "Euro",
    "UEFA European Championship", "FIFA World Cup", "FIFA Club World Cup"
}

TEAM_IDS = {
    "seahawks": 26,
    "mariners": 12,
    "kraken": 90,
}

LEAGUE_IDS = {
    "nfl": 28,
    "nba": 46,
    "nhl": 90,
    "mlb": 10,
    "soccer": 600
}

def fetch_json(url):
    return requests.get(url).json()

def to_pacific_time(iso_str):
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00")).astimezone(PACIFIC)
    return dt.strftime("%m/%d"), dt.strftime("%-I:%M %p")

def get_team_game(team_abbr, include_record=False):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{team_abbr}"
    team_id = TEAM_IDS[team_abbr]
    data = fetch_json(f"https://site.api.espn.com/apis/site/v2/sports/teams/{team_id}")

    next_event = data.get("team", {}).get("nextEvent", [])
    if not next_event:
        events = data.get("team", {}).get("events", [])
        future_events = [e for e in events if datetime.fromisoformat(e["date"].replace("Z", "+00:00")) > datetime.now()]
        next_event = [future_events[0]] if future_events else []

    if not next_event:
        return blank_game()

    event = next_event[0]
    competition = event["competitions"][0]
    competitors = competition["competitors"]
    home = [c for c in competitors if c["homeAway"] == "home"][0]
    away = [c for c in competitors if c["homeAway"] == "away"][0]

    date_str, time_str = to_pacific_time(event["date"])

    return {
        "home_team": home["team"]["displayName"],
        "away_team": away["team"]["displayName"],
        "home_short": home["team"]["shortDisplayName"],
        "away_short": away["team"]["shortDisplayName"],
        "home_score": home.get("score", ""),
        "away_score": away.get("score", ""),
        "home_logo": home["team"]["logo"],
        "away_logo": away["team"]["logo"],
        "home_record": home.get("records", [{}])[0].get("summary", "") if include_record else "",
        "away_record": away.get("records", [{}])[0].get("summary", "") if include_record else "",
        "date": date_str,
        "time": time_str,
        "status": event.get("status", {}).get("type", {}).get("description", "scheduled"),
        "is_live": event.get("status", {}).get("type", {}).get("state") == "in",
        "time_left": event.get("status", {}).get("displayClock", ""),
        "quarter": event.get("status", {}).get("period", "")
    }

def get_league_top_game(league_key):
    league_id = LEAGUE_IDS[league_key]
    url = f"https://site.api.espn.com/apis/site/v2/sports/leagues/{league_id}/scoreboard"
    data = fetch_json(url)
    events = data.get("events", [])

    best = None
    for event in events:
        comp = event["competitions"][0]
        if not best or event["status"]["type"]["id"] == "2":  # prefer live
            best = event

    if not best:
        return blank_game()

    comp = best["competitions"][0]
    home = [c for c in comp["competitors"] if c["homeAway"] == "home"][0]
    away = [c for c in comp["competitors"] if c["homeAway"] == "away"][0]

    date_str, time_str = to_pacific_time(best["date"])

    return {
        "home_team": home["team"]["displayName"],
        "away_team": away["team"]["displayName"],
        "home_short": home["team"]["shortDisplayName"],
        "away_short": away["team"]["shortDisplayName"],
        "home_score": home.get("score", "0"),
        "away_score": away.get("score", "0"),
        "home_logo": home["team"]["logo"],
        "away_logo": away["team"]["logo"],
        "home_record": "",
        "away_record": "",
        "date": date_str,
        "time": time_str,
        "status": best.get("status", {}).get("type", {}).get("description", "Scheduled"),
        "is_live": best.get("status", {}).get("type", {}).get("state") == "in",
        "time_left": best.get("status", {}).get("displayClock", "0:00"),
        "quarter": best.get("status", {}).get("period", 0)
    }

def get_top_soccer_games():
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard"
    data = fetch_json(url)
    now = datetime.now(tz=PACIFIC)

    games = []
    for event in data.get("events", []):
        comp = event["competitions"][0]
        league = comp.get("league", {}).get("name", "")
        home = [c for c in comp["competitors"] if c["homeAway"] == "home"][0]
        away = [c for c in comp["competitors"] if c["homeAway"] == "away"][0]

        start = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).astimezone(PACIFIC)
        if (now - start).total_seconds() > 3 * 3600:  # skip games over 3 hours in past
            continue

        score = 1000
        if league in TOP_SOCCER_LEAGUES:
            score += 1000
        if home["team"]["displayName"] in TOP_SOCCER_TEAMS:
            score += 100
        if away["team"]["displayName"] in TOP_SOCCER_TEAMS:
            score += 100
        score -= abs((start - now).total_seconds()) / 60  # penalize distant games

        date_str, time_str = to_pacific_time(event["date"])

        games.append((score, {
            "home_team": home["team"]["displayName"],
            "away_team": away["team"]["displayName"],
            "home_short": home["team"]["shortDisplayName"],
            "away_short": away["team"]["shortDisplayName"],
            "home_score": home.get("score", "0"),
            "away_score": away.get("score", "0"),
            "home_logo": home["team"]["logo"],
            "away_logo": away["team"]["logo"],
            "home_record": "",
            "away_record": "",
            "date": date_str,
            "time": time_str,
            "status": event.get("status", {}).get("type", {}).get("description", "Scheduled"),
            "is_live": event.get("status", {}).get("type", {}).get("state") == "in",
            "time_left": event.get("status", {}).get("displayClock", "0'"),
            "quarter": event.get("status", {}).get("period", "")
        }))

    top_games = [g[1] for g in sorted(games, reverse=True)[:3]]
    return top_games

def blank_game():
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

def main():
    data = {}
    for team in TEAM_IDS:
        data[team] = get_team_game(team, include_record=True)

    for league in ["nfl", "nba", "nhl", "mlb"]:
        data[league] = get_league_top_game(league)

    data["soccer"] = get_top_soccer_games()

    with open("public/sports.json", "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()