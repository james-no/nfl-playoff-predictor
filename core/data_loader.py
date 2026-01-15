"""
NFL data loading with caching and error handling.
"""

import nflreadpy as nfl
import polars as pl
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple
import os
import pickle

from config import SeasonConfig
from logger import get_logger

logger = get_logger(__name__)


class NFLDataLoader:
    """Load and cache NFL play-by-play data."""
    
    def __init__(self, season: Optional[int] = None):
        """
        Initialize data loader.
        
        Args:
            season: NFL season year (auto-detected if None)
        """
        if season is None:
            self.season, self.phase = SeasonConfig.get_current_season()
            logger.info(f"Auto-detected: {self.season} NFL Season ({self.phase})")
        else:
            self.season = season
            self.phase = "Unknown"
        
        self.cache_dir = ".cache"
        self.cache_file = os.path.join(self.cache_dir, f"pbp_{self.season}.pkl")
        self._pbp_data = None
        
        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def load_play_by_play(self, force_refresh: bool = False) -> pd.DataFrame:
        """
        Load NFL play-by-play data with caching.
        
        Args:
            force_refresh: Force re-download from API
            
        Returns:
            DataFrame with play-by-play data
        """
        # Check cache first
        if not force_refresh and self._pbp_data is not None:
            logger.debug("Using in-memory cached data")
            return self._pbp_data
        
        # Check disk cache
        if not force_refresh and os.path.exists(self.cache_file):
            cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(self.cache_file))
            if cache_age < timedelta(hours=SeasonConfig.CACHE_HOURS):
                logger.info(f"Loading from disk cache (age: {cache_age.total_seconds()/3600:.1f}h)")
                try:
                    with open(self.cache_file, 'rb') as f:
                        self._pbp_data = pickle.load(f)
                    return self._pbp_data
                except Exception as e:
                    logger.warning(f"Cache read failed: {e}, fetching fresh data")
        
        # Fetch from API
        logger.info(f"Fetching {self.season} NFL data from API...")
        try:
            pbp = nfl.load_pbp([self.season])
            
            # Validate data
            actual_seasons = pbp['season'].unique().to_list()
            if actual_seasons[0] != self.season:
                logger.warning(f"Season mismatch: requested {self.season}, got {actual_seasons[0]}")
            
            # Filter to regular season and relevant plays
            pbp_reg = pbp.filter(pl.col('season_type') == 'REG')
            pbp_reg = pbp_reg.filter((pl.col('rush') == 1) | (pl.col('pass') == 1))
            self._pbp_data = pbp_reg.to_pandas()
            
            logger.info(f"Loaded {len(self._pbp_data)} regular season plays")
            
            # Cache to disk
            try:
                with open(self.cache_file, 'wb') as f:
                    pickle.dump(self._pbp_data, f)
                logger.debug(f"Cached data to {self.cache_file}")
            except Exception as e:
                logger.warning(f"Cache write failed: {e}")
            
            return self._pbp_data
            
        except Exception as e:
            logger.error(f"Failed to fetch NFL data: {e}")
            
            # Try to use stale cache as fallback
            if os.path.exists(self.cache_file):
                logger.warning("Using stale cache as fallback")
                try:
                    with open(self.cache_file, 'rb') as f:
                        self._pbp_data = pickle.load(f)
                    return self._pbp_data
                except Exception as cache_err:
                    logger.error(f"Stale cache also failed: {cache_err}")
            
            raise RuntimeError(f"Cannot load NFL data: {e}")
    
    def get_team_plays(self, team: str, pbp: Optional[pd.DataFrame] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get offensive and defensive plays for a team.
        
        Args:
            team: Team abbreviation (e.g., 'DEN')
            pbp: Play-by-play data (loads if None)
            
        Returns:
            Tuple of (offensive_plays, defensive_plays)
        """
        if pbp is None:
            pbp = self.load_play_by_play()
        
        offense = pbp[pbp['posteam'] == team].copy()
        defense = pbp[pbp['defteam'] == team].copy()
        
        logger.debug(f"{team}: {len(offense)} offensive plays, {len(defense)} defensive plays")
        
        return offense, defense
    
    def get_recent_games(self, team: str, num_games: int = 4, 
                        pbp: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Get most recent games for a team.
        
        Args:
            team: Team abbreviation
            num_games: Number of recent games
            pbp: Play-by-play data (loads if None)
            
        Returns:
            DataFrame with recent game plays
        """
        if pbp is None:
            pbp = self.load_play_by_play()
        
        team_plays = pbp[(pbp['posteam'] == team) | (pbp['defteam'] == team)].copy()
        
        # Get last N games
        games = team_plays['game_id'].unique()
        recent_games = games[-num_games:] if len(games) >= num_games else games
        
        recent_plays = team_plays[team_plays['game_id'].isin(recent_games)]
        
        logger.debug(f"{team}: Loaded {len(recent_plays)} plays from last {len(recent_games)} games")
        
        return recent_plays
    
    def get_opponent_adjusted_plays(self, team: str, pbp: Optional[pd.DataFrame] = None) -> dict:
        """
        Get plays adjusted for opponent strength.
        
        Args:
            team: Team abbreviation
            pbp: Play-by-play data (loads if None)
            
        Returns:
            Dict with opponent-adjusted metrics
        """
        if pbp is None:
            pbp = self.load_play_by_play()
        
        offense, defense = self.get_team_plays(team, pbp)
        
        # Calculate opponent EPA
        opponent_def_epa = {}
        for opp in offense['defteam'].unique():
            opp_def = pbp[pbp['defteam'] == opp]
            if len(opp_def) > 0:
                opponent_def_epa[opp] = opp_def['epa'].mean()
        
        opponent_off_epa = {}
        for opp in defense['posteam'].unique():
            opp_off = pbp[pbp['posteam'] == opp]
            if len(opp_off) > 0:
                opponent_off_epa[opp] = opp_off['epa'].mean()
        
        return {
            'opponent_def_epa': opponent_def_epa,
            'opponent_off_epa': opponent_off_epa,
            'num_opponents': len(set(list(opponent_def_epa.keys()) + list(opponent_off_epa.keys())))
        }
    
    def clear_cache(self):
        """Clear cached data."""
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
            logger.info(f"Cleared cache: {self.cache_file}")
        self._pbp_data = None
