"""
Derive small, bounded matchup/context EPA adjustments:
- OL vs DL pass-rush mismatch proxy
- Coverage vs WR explosive fit proxy
- Pace/plays proxy
- Special teams (kicking in wind/cold) proxy

All outputs are tiny EPA deltas and must be capped by AdvancedWeights in config.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict

from config import AdvancedWeights
from logger import get_logger

logger = get_logger(__name__)


def _safe_mean(series: pd.Series, default: float = 0.0) -> float:
    try:
        if len(series) == 0:
            return default
        return float(series.mean())
    except Exception:
        return default


def ol_dl_passrush_mismatch(home_off: pd.DataFrame, home_def: pd.DataFrame,
                             away_off: pd.DataFrame, away_def: pd.DataFrame) -> Dict[str, float]:
    """
    Proxy pass-rush mismatch using sack rate per dropback.
    Uses pbp flags if available; otherwise returns 0.
    Returns small EPA deltas for offense vs opponent pass rush.
    """
    deltas = {"home": 0.0, "away": 0.0}
    if not AdvancedWeights.ENABLED:
        return deltas
    
    # Heuristic: sacks per dropback as proxy for pressure
    def sack_rate(off: pd.DataFrame) -> float:
        if 'qb_hit' in off.columns or 'sack' in off.columns:
            dropbacks = (off['pass'] == 1).sum() if 'pass' in off.columns else 0
            sacks = (off.get('sack', pd.Series([0]*len(off))) == 1).sum()
            return (sacks / dropbacks) if dropbacks > 0 else 0.0
        return 0.0

    home_sack_rate = sack_rate(home_off)
    away_sack_rate = sack_rate(away_off)

    # Relative disadvantage converts to tiny EPA penalties
    # 5% sack-rate gap ~ 0.01 EPA impact
    scale = 0.2
    home_delta = np.clip((away_sack_rate - home_sack_rate) * scale, -AdvancedWeights.MAX_EPA_OL_DL, AdvancedWeights.MAX_EPA_OL_DL)
    away_delta = np.clip((home_sack_rate - away_sack_rate) * scale, -AdvancedWeights.MAX_EPA_OL_DL, AdvancedWeights.MAX_EPA_OL_DL)

    deltas["home"] += float(home_delta)
    deltas["away"] += float(away_delta)
    return deltas


def _per_game_total_epa(team_all: pd.DataFrame, team: str) -> pd.DataFrame:
    off = team_all[team_all['posteam'] == team]
    deff = team_all[team_all['defteam'] == team]
    off_g = off.groupby('game_id')['epa'].mean()
    def_g = deff.groupby('game_id')['epa'].mean()
    # Align indices
    all_ids = sorted(set(off_g.index).union(def_g.index))
    off_series = off_g.reindex(all_ids).fillna(0)
    def_series = def_g.reindex(all_ids).fillna(0)
    total = off_series - def_series
    df = total.to_frame('total_epa')
    # If week exists, use it for ordering
    if 'week' in team_all.columns:
        week_map = team_all.drop_duplicates(subset=['game_id']).set_index('game_id')['week']
        df['week'] = week_map.reindex(df.index)
        df = df.sort_values(by=['week', 'total_epa'])
    return df


def epa_momentum_delta(team: str, team_all: pd.DataFrame, away: bool = False) -> Dict[str, float]:
    deltas = {"home": 0.0, "away": 0.0}
    if not AdvancedWeights.ENABLED:
        return deltas
    try:
        df = _per_game_total_epa(team_all, team)
        vals = df['total_epa'].values
        if len(vals) < 2:
            return deltas
        # Overall mean and recent mean
        overall = float(np.nanmean(vals))
        n = AdvancedWeights.MOMENTUM_WINDOW
        recent_vals = vals[-n:] if len(vals) >= n else vals
        recent_mean = float(np.nanmean(recent_vals))
        recent_vs_season = (recent_mean - overall) * AdvancedWeights.MOMENTUM_RECENT_VS_SEASON_SCALE
        # Slope trend
        x = np.arange(len(recent_vals))
        slope = float(np.polyfit(x, recent_vals[-len(x):], 1)[0]) if len(x) >= 2 else 0.0
        slope_scaled = slope * AdvancedWeights.MOMENTUM_SLOPE_SCALE
        delta = np.clip(recent_vs_season + slope_scaled,
                        -AdvancedWeights.MAX_EPA_MOMENTUM,
                        AdvancedWeights.MAX_EPA_MOMENTUM)
        key = 'away' if away else 'home'
        deltas[key] += float(delta)
        return deltas
    except Exception as e:
        logger.debug(f"momentum calc error for {team}: {e}")
        return deltas


def coverage_wr_fit(home_off: pd.DataFrame, away_def: pd.DataFrame,
                    away_off: pd.DataFrame, home_def: pd.DataFrame) -> Dict[str, float]:
    """
    Proxy coverage-vs-WR explosive fit via explosive pass rate vs explosive-pass allowed.
    """
    deltas = {"home": 0.0, "away": 0.0}
    if not AdvancedWeights.ENABLED:
        return deltas

    def explosive_pass_rate(df: pd.DataFrame) -> float:
        if 'pass' in df.columns and 'yards_gained' in df.columns:
            mask = (df['pass'] == 1)
            plays = df[mask]
            if len(plays) == 0:
                return 0.0
            return (plays['yards_gained'] >= 20).mean()
        return 0.0

    home_explosive = explosive_pass_rate(home_off)
    away_explosive = explosive_pass_rate(away_off)

    def allowed_explosive(def_df: pd.DataFrame) -> float:
        if 'yards_gained' in def_df.columns and 'pass' in def_df.columns:
            plays = def_df[def_df['pass'] == 1]
            if len(plays) == 0:
                return 0.0
            return (plays['yards_gained'] >= 20).mean()
        return 0.0

    home_def_allowed = allowed_explosive(home_def)
    away_def_allowed = allowed_explosive(away_def)

    # Fit advantage: offense explosive vs opponent allowed
    home_fit = home_explosive - away_def_allowed
    away_fit = away_explosive - home_def_allowed

    scale = 0.05  # small
    home_delta = np.clip(home_fit * scale, -AdvancedWeights.MAX_EPA_COVERAGE_FIT, AdvancedWeights.MAX_EPA_COVERAGE_FIT)
    away_delta = np.clip(away_fit * scale, -AdvancedWeights.MAX_EPA_COVERAGE_FIT, AdvancedWeights.MAX_EPA_COVERAGE_FIT)

    deltas["home"] += float(home_delta)
    deltas["away"] += float(away_delta)
    return deltas


def pace_plays_adjustment(home_all: pd.DataFrame, away_all: pd.DataFrame) -> Dict[str, float]:
    """
    Estimate pace via plays-per-game proxies (last N games not implemented here).
    If pace slower than average, slightly compress advantages.
    """
    deltas = {"home": 0.0, "away": 0.0}
    if not AdvancedWeights.ENABLED:
        return deltas

    def plays_per_game(df: pd.DataFrame) -> float:
        games = df['game_id'].nunique() if 'game_id' in df.columns else 1
        return len(df) / max(1, games)

    league_avg = 125.0  # combined plays/game rough avg
    combined = (plays_per_game(home_all) + plays_per_game(away_all))
    # If combined plays low, reduce edge slightly (defenses benefit)
    diff = (combined - league_avg) / league_avg
    compress = np.clip(-diff * 0.01, -AdvancedWeights.MAX_EPA_PACE, AdvancedWeights.MAX_EPA_PACE)

    deltas["home"] += float(compress/2)
    deltas["away"] += float(compress/2)
    return deltas


def special_teams_adjustment(temp_f: float | None = None, wind_mph: float | None = None) -> Dict[str, float]:
    """
    Small kick game adjustment penalty in cold/windy games (hurts total scoring, split).
    """
    deltas = {"home": 0.0, "away": 0.0}
    if not AdvancedWeights.ENABLED:
        return deltas

    penalty = 0.0
    if temp_f is not None and temp_f < 25:
        penalty -= 0.004
    if wind_mph is not None and wind_mph > 18:
        penalty -= 0.004

    penalty = float(np.clip(penalty, -AdvancedWeights.MAX_EPA_SPECIAL_TEAMS, AdvancedWeights.MAX_EPA_SPECIAL_TEAMS))
    deltas["home"] += penalty/2
    deltas["away"] += penalty/2
    return deltas


def aggregate_advanced(home_team: str, away_team: str,
                        home_off: pd.DataFrame, home_def: pd.DataFrame,
                        away_off: pd.DataFrame, away_def: pd.DataFrame,
                        home_all: pd.DataFrame, away_all: pd.DataFrame,
                        weather: Dict | None = None) -> Dict[str, float]:
    """
    Compute sum of advanced deltas with total cap across factors.
    """
    deltas = {"home": 0.0, "away": 0.0}
    if not AdvancedWeights.ENABLED:
        return deltas

    parts = []
    parts.append(ol_dl_passrush_mismatch(home_off, home_def, away_off, away_def))
    parts.append(coverage_wr_fit(home_off, away_def, away_off, home_def))
    parts.append(pace_plays_adjustment(home_all, away_all))

    # Momentum ("hot hand") based on per-game total EPA trend and recent-vs-season diff
    parts.append(epa_momentum_delta(home_team, home_all))
    parts.append(epa_momentum_delta(away_team, away_all, away=True))

    temp = weather.get('temperature') if weather else None
    wind = weather.get('wind_speed') if weather else None
    parts.append(special_teams_adjustment(temp, wind))

    # Sum and cap total
    for d in parts:
        deltas['home'] += d['home']
        deltas['away'] += d['away']

    total = abs(deltas['home']) + abs(deltas['away'])
    if total > AdvancedWeights.MAX_EPA_TOTAL:
        scale = AdvancedWeights.MAX_EPA_TOTAL / total
        deltas['home'] *= scale
        deltas['away'] *= scale
    return deltas
