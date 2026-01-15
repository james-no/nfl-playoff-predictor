"""
EPA analysis with situational stats and recent form.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

from config import EPAConfig, BettingConfig
from logger import get_logger

logger = get_logger(__name__)


class EPAAnalyzer:
    """Analyze EPA metrics for NFL teams."""
    
    def __init__(self):
        """Initialize EPA analyzer."""
        self.config = EPAConfig
    
    def calculate_team_epa(self, offense: pd.DataFrame, defense: pd.DataFrame) -> Dict:
        """
        Calculate comprehensive EPA metrics for a team.
        
        Args:
            offense: Offensive plays DataFrame
            defense: Defensive plays DataFrame
            
        Returns:
            Dict with EPA metrics
        """
        if len(offense) == 0 or len(defense) == 0:
            logger.warning("Empty play data provided")
            return {
                'off_epa': 0.0,
                'def_epa': 0.0,
                'total_epa': 0.0,
                'off_plays': 0,
                'def_plays': 0
            }
        
        off_epa = offense['epa'].mean()
        def_epa = defense['epa'].mean()  # Lower is better for defense
        
        result = {
            'off_epa': off_epa,
            'def_epa': def_epa,
            'total_epa': off_epa - def_epa,  # Total team EPA
            'off_plays': len(offense),
            'def_plays': len(defense),
            
            # Consistency metrics
            'off_epa_std': offense['epa'].std(),
            'def_epa_std': defense['epa'].std(),
            
            # Success rates
            'off_success_rate': (offense['epa'] > 0).mean(),
            'def_success_rate': (defense['epa'] < 0).mean()  # Stop rate
        }
        
        logger.debug(f"EPA calculated: Off={off_epa:.3f}, Def={def_epa:.3f}, Total={result['total_epa']:.3f}")
        
        return result
    
    def calculate_recent_form(self, team: str, recent_plays: pd.DataFrame) -> Dict:
        """
        Calculate recent form (last N games).
        
        Args:
            team: Team abbreviation
            recent_plays: Recent game plays DataFrame
            
        Returns:
            Dict with recent form EPA
        """
        if len(recent_plays) == 0:
            logger.warning(f"{team}: No recent plays available")
            return {'recent_off_epa': 0.0, 'recent_def_epa': 0.0, 'recent_games': 0}
        
        offense = recent_plays[recent_plays['posteam'] == team]
        defense = recent_plays[recent_plays['defteam'] == team]
        
        recent_off_epa = offense['epa'].mean() if len(offense) > 0 else 0.0
        recent_def_epa = defense['epa'].mean() if len(defense) > 0 else 0.0
        
        num_games = len(recent_plays['game_id'].unique())
        
        logger.debug(f"{team} recent form ({num_games} games): Off={recent_off_epa:.3f}, Def={recent_def_epa:.3f}")
        
        return {
            'recent_off_epa': recent_off_epa,
            'recent_def_epa': recent_def_epa,
            'recent_total_epa': recent_off_epa - recent_def_epa,
            'recent_games': num_games
        }
    
    def calculate_situational_stats(self, offense: pd.DataFrame, defense: pd.DataFrame) -> Dict:
        """
        Calculate situational stats: 3rd down, red zone, 4th quarter, 2-minute drill.
        
        Args:
            offense: Offensive plays DataFrame
            defense: Defensive plays DataFrame
            
        Returns:
            Dict with situational EPA metrics
        """
        stats = {}
        
        # 3rd down efficiency
        off_3rd = offense[offense['down'] == 3]
        def_3rd = defense[defense['down'] == 3]
        
        stats['off_3rd_epa'] = off_3rd['epa'].mean() if len(off_3rd) > 0 else 0.0
        stats['def_3rd_epa'] = def_3rd['epa'].mean() if len(def_3rd) > 0 else 0.0
        stats['off_3rd_conv_rate'] = (off_3rd['first_down'] == 1).mean() if len(off_3rd) > 0 else 0.0
        stats['def_3rd_stop_rate'] = (def_3rd['first_down'] == 0).mean() if len(def_3rd) > 0 else 0.0
        
        # Red zone efficiency (inside 20 yard line)
        off_redzone = offense[offense['yardline_100'] <= 20]
        def_redzone = defense[defense['yardline_100'] <= 20]
        
        stats['off_redzone_epa'] = off_redzone['epa'].mean() if len(off_redzone) > 0 else 0.0
        stats['def_redzone_epa'] = def_redzone['epa'].mean() if len(def_redzone) > 0 else 0.0
        stats['off_redzone_td_rate'] = (off_redzone['touchdown'] == 1).mean() if len(off_redzone) > 0 else 0.0
        stats['def_redzone_td_rate'] = (def_redzone['touchdown'] == 1).mean() if len(def_redzone) > 0 else 0.0
        
        # 4th quarter performance
        off_q4 = offense[offense['qtr'] == 4]
        def_q4 = defense[defense['qtr'] == 4]
        
        stats['off_q4_epa'] = off_q4['epa'].mean() if len(off_q4) > 0 else 0.0
        stats['def_q4_epa'] = def_q4['epa'].mean() if len(def_q4) > 0 else 0.0
        
        # 2-minute drill (last 2 minutes of half)
        off_2min = offense[(offense['half_seconds_remaining'] <= 120) & (offense['half_seconds_remaining'] > 0)]
        def_2min = defense[(defense['half_seconds_remaining'] <= 120) & (defense['half_seconds_remaining'] > 0)]
        
        stats['off_2min_epa'] = off_2min['epa'].mean() if len(off_2min) > 0 else 0.0
        stats['def_2min_epa'] = def_2min['epa'].mean() if len(def_2min) > 0 else 0.0
        
        logger.debug(f"Situational stats: 3rd={stats['off_3rd_conv_rate']:.2%}, RZ TD={stats['off_redzone_td_rate']:.2%}")
        
        return stats
    
    def calculate_explosive_plays(self, offense: pd.DataFrame, defense: pd.DataFrame) -> Dict:
        """
        Calculate explosive play rates (20+ yards).
        
        Args:
            offense: Offensive plays DataFrame
            defense: Defensive plays DataFrame
            
        Returns:
            Dict with explosive play metrics
        """
        off_explosive = (offense['yards_gained'] >= 20).sum()
        def_explosive = (defense['yards_gained'] >= 20).sum()
        
        off_explosive_rate = off_explosive / len(offense) if len(offense) > 0 else 0.0
        def_explosive_rate = def_explosive / len(defense) if len(defense) > 0 else 0.0
        
        # EPA from explosive plays
        off_explosive_plays = offense[offense['yards_gained'] >= 20]
        def_explosive_plays = defense[defense['yards_gained'] >= 20]
        
        off_explosive_epa = off_explosive_plays['epa'].mean() if len(off_explosive_plays) > 0 else 0.0
        def_explosive_epa = def_explosive_plays['epa'].mean() if len(def_explosive_plays) > 0 else 0.0
        
        return {
            'off_explosive_rate': off_explosive_rate,
            'def_explosive_rate': def_explosive_rate,
            'off_explosive_epa': off_explosive_epa,
            'def_explosive_epa': def_explosive_epa,
            'off_explosive_count': off_explosive,
            'def_explosive_count': def_explosive
        }
    
    def calculate_opponent_adjusted_epa(self, team_epa: Dict, opponent_data: Dict) -> Dict:
        """
        Adjust EPA for opponent strength.
        
        Args:
            team_epa: Team's EPA metrics
            opponent_data: Opponent strength data
            
        Returns:
            Dict with adjusted EPA
        """
        if not opponent_data or not opponent_data.get('opponent_def_epa'):
            logger.debug("No opponent data, returning unadjusted EPA")
            return team_epa
        
        # Get average opponent defensive EPA
        opp_def_epas = list(opponent_data['opponent_def_epa'].values())
        avg_opp_def_epa = np.mean(opp_def_epas) if opp_def_epas else 0.0
        
        # Adjust offensive EPA based on opponent defense strength
        # If faced tough defenses (negative EPA allowed), boost the offensive EPA
        adjustment = avg_opp_def_epa * 0.3  # 30% weight to SOS
        
        adjusted_off_epa = team_epa['off_epa'] - adjustment
        
        logger.debug(f"Opponent adjustment: {adjustment:.3f}, Adjusted EPA: {adjusted_off_epa:.3f}")
        
        return {
            **team_epa,
            'adjusted_off_epa': adjusted_off_epa,
            'sos_adjustment': adjustment,
            'avg_opp_def_epa': avg_opp_def_epa
        }
    
    def combine_full_and_recent(self, full_epa: Dict, recent_epa: Dict) -> Dict:
        """
        Combine full season and recent form EPA with weighting.
        
        Args:
            full_epa: Full season EPA
            recent_epa: Recent games EPA
            
        Returns:
            Dict with combined weighted EPA
        """
        full_weight = EPAConfig.FULL_SEASON_WEIGHT
        recent_weight = EPAConfig.RECENT_FORM_WEIGHT
        
        combined_off_epa = (full_epa['off_epa'] * full_weight + 
                           recent_epa['recent_off_epa'] * recent_weight)
        combined_def_epa = (full_epa['def_epa'] * full_weight + 
                           recent_epa['recent_def_epa'] * recent_weight)
        
        logger.debug(f"Combined EPA: Off={combined_off_epa:.3f}, Def={combined_def_epa:.3f}")
        
        return {
            'combined_off_epa': combined_off_epa,
            'combined_def_epa': combined_def_epa,
            'combined_total_epa': combined_off_epa - combined_def_epa
        }
    
    def apply_division_rivalry(self, epa_diff: float, is_division_game: bool) -> float:
        """
        Apply division rivalry compression to EPA differential.
        
        Args:
            epa_diff: Raw EPA differential
            is_division_game: Whether this is a division rivalry
            
        Returns:
            Adjusted EPA differential
        """
        if not is_division_game:
            return epa_diff
        
        compression = BettingConfig.DIVISION_RIVALRY_COMPRESSION
        adjusted = epa_diff * (1 - compression)
        
        logger.debug(f"Division rivalry: EPA {epa_diff:.3f} → {adjusted:.3f} ({compression:.0%} compression)")
        
        return adjusted
    
    def apply_rest_advantage(self, epa: float, rest_days_diff: int) -> float:
        """
        Apply rest differential advantage to EPA.
        
        Args:
            epa: Base EPA
            rest_days_diff: Difference in rest days (positive = advantage)
            
        Returns:
            Adjusted EPA with rest factor
        """
        if rest_days_diff == 0:
            return epa
        
        # ~0.5% EPA boost per day of rest advantage
        rest_boost = rest_days_diff * 0.005
        adjusted = epa + rest_boost
        
        logger.debug(f"Rest advantage: {rest_days_diff} days → {rest_boost:+.3f} EPA boost")
        
        return adjusted
