"""
Core prediction engine for NFL Playoff Predictor.

This package contains the main prediction logic organized into modular classes.
"""

from .data_loader import NFLDataLoader
from .epa_analyzer import EPAAnalyzer
from .betting_analyzer import BettingAnalyzer
from .predictor import NFLPredictor

__all__ = ['NFLDataLoader', 'EPAAnalyzer', 'BettingAnalyzer', 'NFLPredictor']
