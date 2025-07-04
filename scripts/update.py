import json
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

TOP_SOCCER_TEAMS = [
    # EPL
    "Manchester City", "Liverpool", "Arsenal", "Manchester United", "Chelsea", "Tottenham Hotspur", "Newcastle United",
    # La Liga
    "Real Madrid", "Barcelona", "Atlético Madrid", "Sevilla",
    # Serie A
    "Inter Milan", "AC Milan", "Juventus", "Napoli", "Roma",
    # Bundesliga
    "Bayern Munich", "Borussia Dortmund", "RB Leipzig", "Bayer Leverkusen",
    # Ligue 1
    "Paris Saint-Germain", "Marseille", "Monaco",
    # Other notables
    "Club América", "Ajax", "Benfica", "Porto"
]

SOCCER_LEAGUES = [
    "eng.1", "esp.1", "ita.1", "ger.1", "fra.1",
    "uefa.champions", "uefa.europa", "fifa.world", "uefa.euro", "fifa.cwc"
]

TEAM_IDS = {
    "seahawks": "26",      # NFL
    "mariners": "12",      # MLB
    "kraken": "55"         # NHL
}

LEAGUE_IDS = {
    "nfl": "28",
    "nba": "23",
    "mlb": "10",
    "nhl": "17"
}

def fetch_json(url):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def convert_time(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00")).astimezone(PACIFIC)
        return dt.strftime("%m/%d"), dt.strftime("%-I:%M %p")
    except Exception:
        return "", ""

def get_team_game(team_id, include_record=False):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}"
    try:
        data = fetch_json(url)
        team = data.get("team", {})
        next_event = team.get("nextEvent", [])
        if not next_event:
            return empty_game()
        game = next_event[0]
        competition = game.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])
        home, away = sorted(competitors, key=lambda x: x["homeAway"] != "home")
        date, time = convert_time(game.get("date", ""))

        return {
            "home_team": home.get("team", {}).get("displayName", ""),
            "away_team": away.get("team", {}).get("displayName", ""),
            "home_short": home.get("team", {}).get("shortDisplayName", ""),
            "away_short": away.get("team", {}).get("shortDisplayName", ""),
            "home_score": home.get("score", ""),
            "away_score": away.get("score", ""),
            "home_logo": home.get("team", {}).get("logo", ""),
            "away_logo": away.get("team", {}).get("logo", ""),
            "home_record": home.get("records", [{}])[0].get("summary", "") if include_record else "",
            "away_record": away.get("records", [{}])[0].get("summary", "") if include_record else "",
            "date": date,
            "time": time,
            "status": game.get("status", {}).get("type", {}).get("description", "").capitalize(),
            "is_live": game.get("status", {}).get("type", {}).get("state", "") == "in",
            "time_left": game.get("status", {}).get("displayClock", ""),
            "quarter": game.get("status", {}).get("period", "")
        }
    except Exception:
        return empty_game()

def get_league_game(league_abbr, league_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{league_abbr}/scoreboard"
    try:
        data = fetch_json(url)
        events = data.get("events", [])
        if not events:
            return empty_game()
        game = events[0]
        competition = game.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])
        home, away = sorted(competitors, key=lambda x: x["homeAway"] != "home")
        date, time = convert_time(game.get("date", ""))

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
            "date": date,
            "time": time,
            "status": game.get("status", {}).get("type", {}).get("description", "").capitalize(),
            "is_live": game.get("status", {}).get("type", {}).get("state", "") == "in",
            "time_left": game.get("status", {}).get("displayClock", ""),
            "quarter": game.get("status", {}).get("period", "")
        }
    except Exception:
        return empty_game()

def get_top_soccer_games():
    games = []
    now = datetime.now(PACIFIC)
    try:
        for league in SOCCER_LEAGUES:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"
            data = fetch_json(url)
            for event in data.get("events", []):
                comp = event.get("competitions", [{}])[0]
                teams = comp.get("competitors", [])
                if len(teams) != 2:
                    continue
                home, away = sorted(teams, key=lambda x: x["homeAway"] != "home")
                home_name = home.get("team", {}).get("displayName", "")
                away_name = away.get("team", {}).get("displayName", "")
                if any(team in TOP_SOCCER_TEAMS for team in [home_name, away_name]):
                    game_time = datetime.fromisoformat(event.get("date", "").replace("Z", "+00:00")).astimezone(PACIFIC)
                    if game_time >= now:
                        date, time = convert_time(event["date"])
                        games.append({
                            "home_team": home_name,
                            "away_team": away_name,
                            "home_short": home.get("team", {}).get("shortDisplayName", ""),
                            "away_short": away.get("team", {}).get("shortDisplayName", ""),
                            "home_score": home.get("score", ""),
                            "away_score": away.get("score", ""),
                            "home_logo": home.get("team", {}).get("logo", ""),
                            "away_logo": away.get("team", {}).get("logo", ""),
                            "home_record": "",
                            "away_record": "",
                            "date": date,
                            "time": time,
                            "status": event.get("status", {}).get("type", {}).get("description", ""),
                            "is_live": event.get("status", {}).get("type", {}).get("state", "") == "in",
                            "time_left": event.get("status", {}).get("displayClock", ""),
                            "quarter": event.get("status", {}).get("period", "")
                        })
        games.sort(key=lambda g: datetime.strptime(g["date"] + " " + g["time"], "%m/%d %I:%M %p"))
    except Exception:
        return []
    return games[:3]

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

def main():
    data = {}
    data["seahawks"] = get_team_game(TEAM_IDS["seahawks"])
    data["mariners"] = get_team_game(TEAM_IDS["mariners"])
    data["kraken"] = get_team_game(TEAM_IDS["kraken"])

    for league, lid in LEAGUE_IDS.items():
        data[league] = get_league_game(league, lid)

    data["soccer"] = get_top_soccer_games()

    with open("sports.json", "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()