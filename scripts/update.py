import json
import requests
from datetime import datetime, timedelta
import pytz

PACIFIC_TZ = pytz.timezone("US/Pacific")

TEAMS = {
    "seahawks": "sea",
    "mariners": "sea",
    "kraken": "sea"
}

LEAGUES = {
    "nfl": "football/nfl",
    "nba": "basketball/nba",
    "nhl": "hockey/nhl",
    "mlb": "baseball/mlb"
}

SOCCER_LEAGUE_URLS = [
    "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fra.1/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.europa/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.euro/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.club/scoreboard"
]

TOP_CLUBS = [
    "Real Madrid", "Barcelona", "Atletico Madrid",
    "Manchester City", "Manchester United", "Liverpool", "Chelsea", "Arsenal", "Tottenham Hotspur",
    "Bayern Munich", "Borussia Dortmund", "RB Leipzig",
    "Juventus", "AC Milan", "Inter Milan", "Napoli",
    "Paris Saint-Germain", "Marseille", "Monaco",
    "Ajax", "Porto", "Benfica"
]

TOP_COMPETITIONS = [
    "Champions League", "World Cup", "Euro", "UEFA Champions", "FIFA World Cup",
    "UEFA European", "UEFA Europa", "FIFA Club", "FIFA Club World Cup"
]

def parse_datetime(iso_str):
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.astimezone(PACIFIC_TZ)

def get_game_from_scoreboard(url):
    try:
        resp = requests.get(url)
        data = resp.json()
        events = data.get("events", [])
        future_events = []
        for event in events:
            try:
                dt = parse_datetime(event["date"])
                if dt > datetime.now(PACIFIC_TZ) - timedelta(hours=3):
                    future_events.append((dt, event))
            except:
                continue
        if not future_events:
            return {}
        future_events.sort()
        dt, event = future_events[0]
        comp = event["competitions"][0]
        competitors = comp["competitors"]
        home = next(t for t in competitors if t["homeAway"] == "home")
        away = next(t for t in competitors if t["homeAway"] == "away")
        status = event["status"]["type"]
        return {
            "home_team": home["team"]["displayName"],
            "away_team": away["team"]["displayName"],
            "home_short": home["team"].get("shortDisplayName", home["team"]["displayName"]),
            "away_short": away["team"].get("shortDisplayName", away["team"]["displayName"]),
            "home_score": home.get("score", ""),
            "away_score": away.get("score", ""),
            "home_logo": home["team"].get("logo", ""),
            "away_logo": away["team"].get("logo", ""),
            "home_record": home.get("records", [{}])[0].get("summary", ""),
            "away_record": away.get("records", [{}])[0].get("summary", ""),
            "date": dt.strftime("%m/%d"),
            "time": dt.strftime("%-I:%M %p"),
            "status": status["description"],
            "is_live": status["state"] == "in",
            "time_left": event["status"].get("displayClock", ""),
            "quarter": event["status"].get("period", "")
        }
    except:
        return {}

def get_team_game(team_abbr, include_record=False):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_abbr}"
    try:
        data = requests.get(url).json()
        next_event = data.get("team", {}).get("nextEvent", [])
        if not next_event:
            return {
                "home_team": "", "away_team": "",
                "home_short": "", "away_short": "",
                "home_score": "", "away_score": "",
                "home_logo": "", "away_logo": "",
                "home_record": "", "away_record": "",
                "date": "", "time": "",
                "status": "scheduled", "is_live": False,
                "time_left": "", "quarter": ""
            }
        event = next_event[0]
        comp = event["competitions"][0]
        competitors = comp["competitors"]
        home = next(t for t in competitors if t["homeAway"] == "home")
        away = next(t for t in competitors if t["homeAway"] == "away")
        dt = parse_datetime(event["date"])
        status = event["status"]["type"]
        return {
            "home_team": home["team"]["displayName"],
            "away_team": away["team"]["displayName"],
            "home_short": home["team"].get("shortDisplayName", home["team"]["displayName"]),
            "away_short": away["team"].get("shortDisplayName", away["team"]["displayName"]),
            "home_score": home.get("score", ""),
            "away_score": away.get("score", ""),
            "home_logo": home["team"].get("logo", ""),
            "away_logo": away["team"].get("logo", ""),
            "home_record": home.get("records", [{}])[0].get("summary", "") if include_record else "",
            "away_record": away.get("records", [{}])[0].get("summary", "") if include_record else "",
            "date": dt.strftime("%m/%d"),
            "time": dt.strftime("%-I:%M %p"),
            "status": status["description"],
            "is_live": status["state"] == "in",
            "time_left": event["status"].get("displayClock", ""),
            "quarter": event["status"].get("period", "")
        }
    except:
        return {
            "home_team": "", "away_team": "",
            "home_short": "", "away_short": "",
            "home_score": "", "away_score": "",
            "home_logo": "", "away_logo": "",
            "home_record": "", "away_record": "",
            "date": "", "time": "",
            "status": "scheduled", "is_live": False,
            "time_left": "", "quarter": ""
        }

def get_soccer_score(event):
    alt_names = [
        event.get("name", ""),
        event.get("shortName", ""),
        event.get("group", {}).get("name", ""),
        event.get("league", {}).get("name", ""),
        event.get("season", {}).get("name", ""),
    ]
    teams = [t["team"]["displayName"] for t in event.get("competitions", [{}])[0].get("competitors", [])]
    top_club_bonus = sum(1 for t in teams if t in TOP_CLUBS)
    competition_bonus = any(any(tc.lower() in alt.lower() for alt in alt_names) for tc in TOP_COMPETITIONS)
    try:
        start_dt = parse_datetime(event["date"])
        time_to_game = (start_dt - datetime.now(PACIFIC_TZ)).total_seconds() / 3600
    except:
        time_to_game = float("inf")

    score = (
        (100 if competition_bonus else 0) +
        20 * top_club_bonus -
        0.1 * max(time_to_game, 0)
    )
    return score

def get_top_soccer_games():
    all_games = []
    for url in SOCCER_LEAGUE_URLS:
        try:
            resp = requests.get(url)
            data = resp.json()
            for event in data.get("events", []):
                comp = event.get("competitions", [{}])[0]
                competitors = comp.get("competitors", [])
                if len(competitors) != 2:
                    continue
                teams = sorted(competitors, key=lambda x: x["homeAway"])
                home, away = teams[0], teams[1]
                game = {
                    "home_team": home["team"]["displayName"],
                    "away_team": away["team"]["displayName"],
                    "home_short": home["team"].get("shortDisplayName", home["team"]["displayName"]),
                    "away_short": away["team"].get("shortDisplayName", away["team"]["displayName"]),
                    "home_score": home.get("score", ""),
                    "away_score": away.get("score", ""),
                    "home_logo": home["team"]["logo"],
                    "away_logo": away["team"]["logo"],
                    "home_record": home["records"][0]["summary"] if home.get("records") else "",
                    "away_record": away["records"][0]["summary"] if away.get("records") else "",
                    "date": "",
                    "time": "",
                    "status": event.get("status", {}).get("type", {}).get("description", ""),
                    "is_live": event.get("status", {}).get("type", {}).get("state") == "in",
                    "time_left": event.get("status", {}).get("displayClock", ""),
                    "quarter": event.get("status", {}).get("period", "")
                }
                try:
                    dt = parse_datetime(event["date"])
                    if dt < datetime.now(PACIFIC_TZ) - timedelta(days=1):
                        continue
                    game["date"] = dt.strftime("%m/%d")
                    game["time"] = dt.strftime("%-I:%M %p")
                except:
                    continue
                game["score_value"] = get_soccer_score(event)
                all_games.append(game)
        except:
            continue
    top_games = sorted(all_games, key=lambda g: -g["score_value"])
    return top_games[:3]

def main():
    data = {}
    for team, abbr in TEAMS.items():
        data[team] = get_team_game(abbr)

    for league, path in LEAGUES.items():
        url = f"https://site.api.espn.com/apis/site/v2/sports/{path}/scoreboard"
        data[league] = get_game_from_scoreboard(url)

    data["soccer"] = get_top_soccer_games()

    with open("sports.json", "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()