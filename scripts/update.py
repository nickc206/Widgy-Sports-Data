import requests
import json
from datetime import datetime, timedelta
from pytz import timezone

# Constants
PACIFIC = timezone("US/Pacific")
TODAY = datetime.now(PACIFIC).date()
THREE_DAYS_OUT = TODAY + timedelta(days=3)

TOP_CLUBS = {
    "Real Madrid", "Barcelona", "Manchester City", "Manchester United", "Arsenal",
    "Liverpool", "Chelsea", "Tottenham", "Bayern Munich", "Borussia Dortmund",
    "PSG", "Marseille", "Juventus", "Napoli", "AC Milan", "Inter Milan", "Ajax",
    "Porto", "Benfica", "Atletico Madrid", "RB Leipzig", "Roma", "Lazio", "Sevilla",
    "Bologna"
}

TOP_COUNTRIES = {
    "Argentina", "Brazil", "France", "Germany", "Spain", "England", "Italy", "Belgium",
    "Portugal", "Netherlands", "Uruguay"
}

def fetch_json(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None

def extract_game(event):
    event_dt = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).astimezone(PACIFIC)
    competition = event.get("league", {}).get("name", "")
    return {
        "home_team": event["competitions"][0]["competitors"][0]["team"]["displayName"],
        "away_team": event["competitions"][0]["competitors"][1]["team"]["displayName"],
        "home_short": event["competitions"][0]["competitors"][0]["team"]["shortDisplayName"],
        "away_short": event["competitions"][0]["competitors"][1]["team"]["shortDisplayName"],
        "home_score": event["competitions"][0]["competitors"][0].get("score", "0"),
        "away_score": event["competitions"][0]["competitors"][1].get("score", "0"),
        "home_logo": event["competitions"][0]["competitors"][0]["team"]["logo"],
        "away_logo": event["competitions"][0]["competitors"][1]["team"]["logo"],
        "home_record": event["competitions"][0]["competitors"][0]["records"][0]["summary"]
            if event["competitions"][0]["competitors"][0].get("records") else "",
        "away_record": event["competitions"][0]["competitors"][1]["records"][0]["summary"]
            if event["competitions"][0]["competitors"][1].get("records") else "",
        "date": event_dt.strftime("%m/%d"),
        "time": event_dt.strftime("%-I:%M %p"),
        "status": event["status"]["type"]["description"].lower(),
        "is_live": event["status"]["type"]["state"] == "in",
        "time_left": event["status"].get("displayClock", ""),
        "quarter": event["status"].get("period", "")
    }

def get_league_game(league_slug):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{league_slug}/scoreboard"
    data = fetch_json(url)
    if not data or "events" not in data:
        return empty_game()
    events = data["events"]
    if not events:
        return empty_game()
    return extract_game(events[0])

def get_team_game(team_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams/{team_id}"
    data = fetch_json(url)
    if not data:
        return empty_game()
    next_event = data.get("team", {}).get("nextEvent", [])
    if not next_event:
        return empty_game()
    event = next_event[0]
    event["date"] = event.get("date", datetime.now().isoformat())
    return extract_game(event)

def empty_game():
    return {
        "home_team": "", "away_team": "",
        "home_short": "", "away_short": "",
        "home_score": "", "away_score": "",
        "home_logo": "", "away_logo": "",
        "home_record": "", "away_record": "",
        "date": "", "time": "",
        "status": "scheduled",
        "is_live": False,
        "time_left": "", "quarter": ""
    }

def get_top_soccer_games():
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard"
    data = fetch_json(url)
    if not data or "events" not in data:
        return []

    events = data["events"]
    scored = []

    for event in events:
        if "competitions" not in event or not event["competitions"]:
            continue
        comp = event["competitions"][0]
        if "competitors" not in comp or len(comp["competitors"]) < 2:
            continue

        teams = {
            comp["competitors"][0]["team"]["displayName"],
            comp["competitors"][1]["team"]["displayName"]
        }

        date_str = event.get("date", "")
        if not date_str:
            continue

        event_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(PACIFIC)
        days_until = (event_dt.date() - TODAY).days

        score = 0
        if teams & TOP_CLUBS or teams & TOP_COUNTRIES:
            score += 100
        if "champions league" in comp.get("league", {}).get("name", "").lower():
            score += 10
        if "world cup" in comp.get("league", {}).get("name", "").lower():
            score += 9
        if "euro" in comp.get("league", {}).get("name", "").lower():
            score += 8
        if "europa" in comp.get("league", {}).get("name", "").lower():
            score += 7
        if "friendly" in comp.get("league", {}).get("name", "").lower():
            score -= 1
        if days_until > 3:
            score -= 100

        scored.append((score, event_dt, event))

    top = sorted(scored, key=lambda x: (-x[0], x[1]))
    return [extract_game(e[2]) for e in top[:3]]

def main():
    result = {
        "seahawks": get_team_game("sea"),
        "mariners": get_team_game("sea"),
        "kraken": get_team_game("sea"),
        "nfl": get_league_game("football/nfl"),
        "nba": get_league_game("basketball/nba"),
        "mlb": get_league_game("baseball/mlb"),
        "nhl": get_league_game("hockey/nhl"),
        "soccer": get_top_soccer_games()
    }

    with open("sports.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()