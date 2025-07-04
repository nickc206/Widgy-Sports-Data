import json
import requests
from datetime import datetime, timedelta
from pytz import timezone

PT = timezone("US/Pacific")

TEAM_URLS = {
    "seahawks": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/sea",
    "kraken": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/sea",
    "mariners": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/sea"
}

LEAGUE_URLS = {
    "nfl": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "nba": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
    "mlb": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
    "nhl": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
}

TOP_CLUB_TEAMS = [
    "manchester-city", "real-madrid", "barcelona", "bayern-munich", "psg",
    "juventus", "liverpool", "arsenal", "chelsea", "tottenham-hotspur",
    "ac-milan", "inter-milan", "napoli", "dortmund", "atletico-madrid",
    "marseille", "ajax", "bologna"
]

TOP_COUNTRIES = [
    "brazil", "france", "germany", "spain", "italy",
    "argentina", "england", "belgium"
]

SOCCER_TEAMS = TOP_CLUB_TEAMS + TOP_COUNTRIES
SOCCER_API_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

def fetch_json(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def format_event(event):
    event_dt = datetime.fromisoformat(event["date"][:-1]).astimezone(PT)
    competitors = event["competitions"][0]["competitors"]
    home = next(team for team in competitors if team["homeAway"] == "home")
    away = next(team for team in competitors if team["homeAway"] == "away")
    status = event["status"]["type"]["name"]
    return {
        "home_team": home["team"]["displayName"],
        "away_team": away["team"]["displayName"],
        "home_short": home["team"].get("shortDisplayName", home["team"]["displayName"]),
        "away_short": away["team"].get("shortDisplayName", away["team"]["displayName"]),
        "home_score": home.get("score", ""),
        "away_score": away.get("score", ""),
        "home_logo": home["team"]["logos"][0]["href"] if "logos" in home["team"] else "",
        "away_logo": away["team"]["logos"][0]["href"] if "logos" in away["team"] else "",
        "home_record": home.get("records", [{}])[0].get("summary", ""),
        "away_record": away.get("records", [{}])[0].get("summary", ""),
        "date": event_dt.strftime("%m/%d"),
        "time": event_dt.strftime("%I:%M %p").lstrip("0"),
        "status": status.lower(),
        "is_live": status == "STATUS_IN_PROGRESS",
        "time_left": event["status"].get("displayClock", ""),
        "quarter": event["status"].get("period", "")
    }

def empty_game():
    return {
        "home_team": "", "away_team": "", "home_short": "", "away_short": "",
        "home_score": "", "away_score": "", "home_logo": "", "away_logo": "",
        "home_record": "", "away_record": "", "date": "", "time": "",
        "status": "scheduled", "is_live": False, "time_left": "", "quarter": ""
    }

def get_team_next_game(team_url):
    try:
        data = fetch_json(team_url)
        events = data.get("team", {}).get("nextEvent", [])
        if not events:
            return empty_game()
        return format_event(events[0])
    except:
        return empty_game()

def get_league_next_game(league_url):
    try:
        data = fetch_json(league_url)
        events = data.get("events", [])
        if not events:
            return empty_game()
        return format_event(events[0])
    except:
        return empty_game()

def get_top_soccer_games():
    games = []
    fallback_games = []
    three_days_from_now = datetime.now(PT) + timedelta(days=3)

    for team in SOCCER_TEAMS:
        try:
            url = f"{SOCCER_API_BASE}/teams/{team}"
            data = fetch_json(url)
            events = data.get("team", {}).get("nextEvent", [])
            if not events:
                continue
            event = events[0]
            event_dt = datetime.fromisoformat(event["date"][:-1]).astimezone(PT)
            formatted = format_event(event)
            if event_dt <= three_days_from_now:
                games.append(formatted)
                if len(games) == 3:
                    return games
            else:
                fallback_games.append((event_dt, formatted))
        except:
            continue

    fallback_games.sort(key=lambda x: x[0])
    return games + [g for _, g in fallback_games[:3 - len(games)]]

def main():
    result = {
        "seahawks": get_team_next_game(TEAM_URLS["seahawks"]),
        "mariners": get_team_next_game(TEAM_URLS["mariners"]),
        "kraken": get_team_next_game(TEAM_URLS["kraken"]),
        "nfl": get_league_next_game(LEAGUE_URLS["nfl"]),
        "nba": get_league_next_game(LEAGUE_URLS["nba"]),
        "mlb": get_league_next_game(LEAGUE_URLS["mlb"]),
        "nhl": get_league_next_game(LEAGUE_URLS["nhl"]),
        "soccer": get_top_soccer_games()
    }

    with open("sports.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()