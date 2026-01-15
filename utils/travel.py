"""Travel and crowd noise utilities."""

from typing import Tuple
from config import TeamsConfig, TravelConfig, BettingConfig


_TZ_ORDER = {'ET': 0, 'CT': 1, 'MT': 2, 'PT': 3}


def get_timezones(home_team: str, away_team: str) -> Tuple[str, str]:
    """Return timezones for home and away teams (ET/CT/MT/PT)."""
    home_tz = TeamsConfig.TEAM_TIMEZONES.get(home_team)
    away_tz = TeamsConfig.TEAM_TIMEZONES.get(away_team)
    if home_tz is None or away_tz is None:
        raise ValueError(f"Missing timezone for {home_team} or {away_team}")
    return home_tz, away_tz


def timezone_diff(home_team: str, away_team: str) -> int:
    """Return absolute timezone difference in zones between home and away."""
    home_tz, away_tz = get_timezones(home_team, away_team)
    return abs(_TZ_ORDER[home_tz] - _TZ_ORDER[away_tz])


def compute_travel_penalty(home_team: str, away_team: str, away_rest_days: int | None = None) -> float:
    """
    Compute EPA travel penalty applied to AWAY team based on timezone difference
    and whether the away team is on a short week.
    """
    diff = timezone_diff(home_team, away_team)
    base = TravelConfig.TZ_DIFF_PENALTY.get(diff, 0.0)
    if away_rest_days is not None and away_rest_days < 7:
        base *= TravelConfig.SHORT_WEEK_MULTIPLIER
    return base  # negative or zero


def compute_fan_noise_boost(home_team: str) -> float:
    """
    Compute EPA boost for home team from crowd noise.
    """
    boost = BettingConfig.FAN_NOISE_BASE_EPA
    if home_team in TeamsConfig.LOUD_STADIUMS:
        boost += BettingConfig.FAN_NOISE_LOUD_STADIUM_BONUS_EPA
    if home_team in TeamsConfig.DOME_TEAMS:
        boost += BettingConfig.FAN_NOISE_DOME_BONUS_EPA
    return boost
