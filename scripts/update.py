import requests
import json
from datetime import datetime
from pytz import timezone

OUTPUT_PATH = "sports.json"

def format_game(game):
    def fmt_time(dt):
        pacific = timezone("US/Pacific")
        local_time = datetime.fromisoformat(dt[:-1]).astimezone(pacific)
        return {
            "start_date": local_time.strftime("%m/%d"),
            "start_time": local_time.strftime("%I:%M %p").lstrip("0"),
            "start_time_iso": dt
        }

    return {
        "home_team": game["home_team"],
        "away_team": game["away_team"],
        "home_score": game.get("home_score", ""),
        "away_score": game.get("away_score", ""),
        "league": game.get("league", ""),
        "status": game.get("status", "scheduled"),
        "is_live": game.get("is_live", False),
        "time_left": game.get("time_left", ""),
        "period": game.get("period", ""),
        "short_name_home": game.get("short_name_home", ""),
        "short_name_away": game.get("short_name_away", ""),
        "home_logo": game.get("home_logo", ""),
        "away_logo": game.get("away_logo", ""),
        "record_home": game.get("record_home", ""),
        "record_away": game.get("record_away", ""),
        "venue_indicator": game.get("venue_indicator", "vs"),  # "vs" or "@"
        **fmt_time(game["start_time"])
    }

def get_sports_data():
    # This function will return all 9 blocks of content: 3 teams + 4 leagues + 3 soccer (1 excluded for teams overlap)
    return {
        "seahawks": format_game(fetch_team_game("seahawks")),
        "mariners": format_game(fetch_team_game("mariners")),
        "kraken": format_game(fetch_team_game("kraken")),
        "nfl": format_game(fetch_league_game("nfl")),
        "nba": format_game(fetch_league_game("nba")),
        "mlb": format_game(fetch_league_game("mlb")),
        "nhl": format_game(fetch_league_game("nhl")),
        "top_soccer_1": format_game(fetch_top_soccer_game(0)),
        "top_soccer_2": format_game(fetch_top_soccer_game(1)),
        "top_soccer_3": format_game(fetch_top_soccer_game(2)),
        "top_game_of_day": format_game(fetch_overall_top_game())
    }

# These placeholder functions need to be implemented:
def fetch_team_game(team):
    # Placeholder for actual ESPN scraping/API logic
    return {
        "home_team": "Seattle Seahawks",
        "away_team": "San Francisco 49ers",
        "home_score": "17",
        "away_score": "20",
        "start_time": "2025-09-21T17:20:00Z",
        "league": "NFL",
        "status": "scheduled",
        "is_live": False,
        "record_home": "0-0",
        "record_away": "0-0",
        "short_name_home": "SEA",
        "short_name_away": "SF",
        "home_logo": "https://example.com/sea.png",
        "away_logo": "https://example.com/sf.png",
        "venue_indicator": "vs"
    }

def fetch_league_game(league):
    return fetch_team_game(league)

def fetch_top_soccer_game(rank):
    return fetch_team_game(f"soccer-{rank}")

def fetch_overall_top_game():
    return fetch_team_game("top")

# Main execution
if __name__ == "__main__":
    data = get_sports_data()
    with open(OUTPUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
