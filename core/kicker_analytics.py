"""
Kicker Performance Analytics
Models kicker differential impact on close games using FG% by distance and weather.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple

from config import KickerConfig, TeamsConfig
from logger import get_logger

logger = get_logger(__name__)


def calculate_kicker_stats(pbp: pd.DataFrame, team: str) -> Dict[str, float]:
    """
    Calculate team kicker stats from play-by-play data.
    
    Args:
        pbp: Play-by-play DataFrame
        team: Team abbreviation
        
    Returns:
        Dict with FG% by distance range and overall stats
    """
    if not KickerConfig.ENABLED:
        return {}
    
    # Check if required columns exist
    required_cols = ['posteam', 'field_goal_attempt', 'kick_distance', 'field_goal_result']
    missing_cols = [col for col in required_cols if col not in pbp.columns]
    if missing_cols:
        logger.warning(f"Missing kicker columns for {team}: {missing_cols}. Using defaults.")
        return _default_kicker_stats()
    
    # Filter to field goal attempts by this team
    try:
        team_fgs = pbp[
            (pbp['posteam'] == team) & 
            (pbp['field_goal_attempt'] == 1)
        ].copy()
    except Exception as e:
        logger.warning(f"Error filtering FG data for {team}: {e}")
        return _default_kicker_stats()
    
    if len(team_fgs) == 0:
        logger.debug(f"No FG attempts found for {team}")
        return _default_kicker_stats()
    
    stats = {}
    
    # Calculate FG% by distance range
    for range_name, (min_dist, max_dist) in KickerConfig.DISTANCE_RANGES.items():
        range_fgs = team_fgs[
            (team_fgs['kick_distance'] >= min_dist) & 
            (team_fgs['kick_distance'] <= max_dist)
        ]
        
        if len(range_fgs) > 0:
            makes = (range_fgs['field_goal_result'] == 'made').sum()
            attempts = len(range_fgs)
            pct = makes / attempts
            stats[f'fg_pct_{range_name}'] = pct
            stats[f'fg_attempts_{range_name}'] = attempts
        else:
            # Use league average if no attempts
            stats[f'fg_pct_{range_name}'] = KickerConfig.LEAGUE_AVG_FG_PCT.get(range_name, 0.80)
            stats[f'fg_attempts_{range_name}'] = 0
    
    # Overall FG%
    total_makes = (team_fgs['field_goal_result'] == 'made').sum()
    total_attempts = len(team_fgs)
    stats['fg_pct_overall'] = total_makes / total_attempts if total_attempts > 0 else 0.85
    stats['fg_attempts_total'] = total_attempts
    
    # Clutch performance (4Q or OT)
    clutch_fgs = team_fgs[
        ((team_fgs['qtr'] == 4) | (team_fgs['qtr'] == 5)) &
        (team_fgs['score_differential'].abs() <= 8)  # Within one score
    ]
    
    if len(clutch_fgs) > 3:  # Need minimum sample
        clutch_makes = (clutch_fgs['field_goal_result'] == 'made').sum()
        clutch_attempts = len(clutch_fgs)
        stats['fg_pct_clutch'] = clutch_makes / clutch_attempts
        stats['clutch_attempts'] = clutch_attempts
    else:
        stats['fg_pct_clutch'] = stats['fg_pct_overall']
        stats['clutch_attempts'] = len(clutch_fgs)
    
    return stats


def _default_kicker_stats() -> Dict[str, float]:
    """Return league average kicker stats when no data available."""
    stats = {}
    for range_name, avg_pct in KickerConfig.LEAGUE_AVG_FG_PCT.items():
        stats[f'fg_pct_{range_name}'] = avg_pct
        stats[f'fg_attempts_{range_name}'] = 0
    stats['fg_pct_overall'] = 0.85
    stats['fg_attempts_total'] = 0
    stats['fg_pct_clutch'] = 0.85
    stats['clutch_attempts'] = 0
    return stats


def adjust_for_weather(
    base_fg_pct: float,
    weather: Optional[Dict]
) -> float:
    """
    Adjust FG% for weather conditions.
    
    Args:
        base_fg_pct: Base field goal percentage
        weather: Dict with temperature, wind_speed, precipitation
        
    Returns:
        Weather-adjusted FG%
    """
    if not weather:
        return base_fg_pct
    
    penalty = 0.0
    
    temp = weather.get('temperature', 70)
    wind = weather.get('wind_speed', 0)
    precip = weather.get('precipitation', 0)
    
    # Wind impact (most important for kicking)
    if wind > 25:
        penalty += KickerConfig.WEATHER_PENALTY['wind_extreme']
    elif wind > 15:
        penalty += KickerConfig.WEATHER_PENALTY['wind_high']
    
    # Temperature impact
    if temp < 20:
        penalty += KickerConfig.WEATHER_PENALTY['extreme_cold']
    elif temp < 32:
        penalty += KickerConfig.WEATHER_PENALTY['cold']
    
    # Precipitation
    if precip > 0:
        penalty += KickerConfig.WEATHER_PENALTY['precipitation']
    
    adjusted_pct = max(0.0, base_fg_pct - penalty)
    
    return adjusted_pct


def calculate_kicker_advantage(
    home_stats: Dict[str, float],
    away_stats: Dict[str, float],
    weather: Optional[Dict] = None,
    is_playoff: bool = False
) -> Tuple[float, Dict[str, any]]:
    """
    Calculate EPA advantage from kicker differential.
    
    Args:
        home_stats: Home team kicker stats
        away_stats: Away team kicker stats
        weather: Weather conditions dict
        is_playoff: Whether this is a playoff game
        
    Returns:
        Tuple of (epa_differential, breakdown_dict)
    """
    if not KickerConfig.ENABLED or not home_stats or not away_stats:
        return 0.0, {}
    
    # Focus on medium and long range (40+ yards) - most impactful
    critical_ranges = ['medium', 'long']
    
    home_avg_pct = np.mean([
        home_stats.get(f'fg_pct_{r}', KickerConfig.LEAGUE_AVG_FG_PCT[r])
        for r in critical_ranges
    ])
    
    away_avg_pct = np.mean([
        away_stats.get(f'fg_pct_{r}', KickerConfig.LEAGUE_AVG_FG_PCT[r])
        for r in critical_ranges
    ])
    
    # Adjust for weather
    home_adj_pct = adjust_for_weather(home_avg_pct, weather)
    away_adj_pct = adjust_for_weather(away_avg_pct, weather)
    
    # Adjust for clutch performance in playoffs
    if is_playoff:
        home_clutch = home_stats.get('fg_pct_clutch', home_avg_pct)
        away_clutch = away_stats.get('fg_pct_clutch', away_avg_pct)
        
        # Weight clutch performance more heavily in playoffs
        home_adj_pct = 0.7 * home_adj_pct + 0.3 * home_clutch
        away_adj_pct = 0.7 * away_adj_pct + 0.3 * away_clutch
    
    # Calculate percentage point differential
    pct_point_diff = home_adj_pct - away_adj_pct
    
    # Convert to EPA
    # Expected FG attempts per game × 3 points × differential
    # Close games have more FG attempts
    fg_attempts = KickerConfig.AVG_FG_ATTEMPTS_PER_GAME
    if is_playoff:
        fg_attempts *= KickerConfig.CLOSE_GAME_FG_WEIGHT
    
    # EPA = (FG attempts × 3 points × differential%) / EPA_to_points conversion
    # Then scale by EPA_PER_FG_PCT_POINT
    raw_epa_diff = pct_point_diff * 100 * KickerConfig.EPA_PER_FG_PCT_POINT
    
    # Cap the impact
    epa_diff = np.clip(
        raw_epa_diff,
        -KickerConfig.MAX_KICKER_EPA_DIFF,
        KickerConfig.MAX_KICKER_EPA_DIFF
    )
    
    breakdown = {
        'home_fg_pct': home_avg_pct,
        'away_fg_pct': away_avg_pct,
        'home_adjusted_pct': home_adj_pct,
        'away_adjusted_pct': away_adj_pct,
        'pct_point_diff': pct_point_diff,
        'raw_epa': raw_epa_diff,
        'capped_epa': epa_diff,
        'weather_adjusted': weather is not None,
        'playoff_clutch_weighted': is_playoff
    }
    
    return epa_diff, breakdown


def get_kicker_summary(
    home_team: str,
    away_team: str,
    home_stats: Dict[str, float],
    away_stats: Dict[str, float],
    epa_diff: float,
    breakdown: Dict
) -> str:
    """
    Generate human-readable kicker advantage summary.
    
    Args:
        home_team: Home team abbrev
        away_team: Away team abbrev
        home_stats: Home kicker stats
        away_stats: Away kicker stats
        epa_diff: EPA differential
        breakdown: Breakdown dict from calculate_kicker_advantage
        
    Returns:
        Formatted summary string
    """
    if abs(epa_diff) < 0.005:
        return "Kicker advantage: Negligible"
    
    advantage_team = home_team if epa_diff > 0 else away_team
    
    home_pct = breakdown['home_adjusted_pct']
    away_pct = breakdown['away_adjusted_pct']
    
    summary = f"Kicker advantage: {advantage_team} ({abs(epa_diff):+.3f} EPA)\n"
    summary += f"  {home_team} FG%: {home_pct:.1%} (40+ yards)"
    
    if breakdown['weather_adjusted']:
        summary += " [weather-adjusted]"
    
    summary += f"\n  {away_team} FG%: {away_pct:.1%} (40+ yards)"
    
    if breakdown['weather_adjusted']:
        summary += " [weather-adjusted]"
    
    if breakdown['playoff_clutch_weighted']:
        summary += "\n  Clutch performance weighted for playoff situation"
    
    return summary


# 2025 Season Kicker Data (manually curated - use real data if available)
TEAM_KICKERS_2025 = {
    # AFC
    'KC': {'name': 'Harrison Butker', 'tier': 'elite'},
    'BUF': {'name': 'Tyler Bass', 'tier': 'above_avg'},
    'BAL': {'name': 'Justin Tucker', 'tier': 'elite'},
    'HOU': {'name': 'Ka\'imi Fairbairn', 'tier': 'above_avg'},
    'DEN': {'name': 'Wil Lutz', 'tier': 'above_avg'},
    'NE': {'name': 'Joey Slye', 'tier': 'average'},
    
    # NFC
    'DET': {'name': 'Jake Bates', 'tier': 'average'},
    'PHI': {'name': 'Jake Elliott', 'tier': 'above_avg'},
    'LA': {'name': 'Joshua Karty', 'tier': 'below_avg'},
    'WAS': {'name': 'Zane Gonzalez', 'tier': 'average'},
    'SF': {'name': 'Jake Moody', 'tier': 'average'},
    'SEA': {'name': 'Jason Myers', 'tier': 'above_avg'},
    'CHI': {'name': 'Cairo Santos', 'tier': 'average'},
}


def get_kicker_tier_adjustment(team: str) -> float:
    """
    Manual tier adjustment for known elite/poor kickers.
    Use when play-by-play data is insufficient.
    
    Returns:
        EPA adjustment (-0.01 to +0.01)
    """
    kicker_info = TEAM_KICKERS_2025.get(team, {'tier': 'average'})
    tier = kicker_info['tier']
    
    tier_adjustments = {
        'elite': 0.008,       # Tucker, Butker level
        'above_avg': 0.004,   # Solid veteran
        'average': 0.0,
        'below_avg': -0.004,
        'poor': -0.008
    }
    
    return tier_adjustments.get(tier, 0.0)
