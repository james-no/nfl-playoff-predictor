"""Betting intelligence and analysis."""

from typing import Dict, Optional
from utils.kelly import KellyCalculator
from config import BettingConfig
from logger import get_logger

logger = get_logger(__name__)


class BettingAnalyzer:
    """Analyze betting angles and calculate optimal bet sizing."""
    
    def __init__(self):
        """Initialize betting analyzer."""
        self.kelly_calc = KellyCalculator()
        self.key_numbers = BettingConfig.KEY_NUMBERS
    
    def calculate_betting_recommendation(self, win_prob: float, spread: float, 
                                        odds: int = -110, bankroll: float = 10000) -> Dict:
        """
        Generate complete betting recommendation.
        
        Args:
            win_prob: Win probability (0-1)
            spread: Point spread
            odds: American odds (default -110)
            bankroll: Total bankroll
            
        Returns:
            Dict with betting recommendation
        """
        kelly_result = self.kelly_calc.calculate_bet_size(win_prob, odds, bankroll)
        key_number_analysis = self.analyze_key_numbers(spread)
        
        return {
            **kelly_result,
            'spread': spread,
            'odds': odds,
            'key_number_analysis': key_number_analysis
        }
    
    def analyze_key_numbers(self, spread: float) -> Dict:
        """
        Analyze if spread is near key numbers (3, 7, 10).
        
        Args:
            spread: Point spread
            
        Returns:
            Dict with key number analysis
        """
        abs_spread = abs(spread)
        nearest_key = min(self.key_numbers, key=lambda x: abs(x - abs_spread))
        distance = abs(abs_spread - nearest_key)
        
        is_key_number = distance < 0.5
        at_risk = 0.5 <= distance < 1.0
        
        analysis = {
            'spread': spread,
            'abs_spread': abs_spread,
            'nearest_key_number': nearest_key,
            'distance_from_key': distance,
            'is_key_number': is_key_number,
            'at_risk_of_push': at_risk
        }
        
        if is_key_number:
            logger.debug(f"Spread {spread} is AT key number {nearest_key}")
        elif at_risk:
            logger.debug(f"Spread {spread} is NEAR key number {nearest_key} (distance: {distance:.1f})")
        
        return analysis
    
    def calculate_clv(self, bet_spread: float, closing_spread: float) -> float:
        """
        Calculate Closing Line Value.
        
        Args:
            bet_spread: Spread when bet was placed
            closing_spread: Closing line spread
            
        Returns:
            CLV in points (positive = beat closing line)
        """
        clv = abs(closing_spread) - abs(bet_spread)
        
        if clv > 0:
            logger.info(f"Positive CLV: {clv:+.1f} points")
        elif clv < 0:
            logger.warning(f"Negative CLV: {clv:.1f} points")
        
        return clv
    
    def analyze_sharp_money(self, opening_line: float, current_line: float, 
                           bet_percentage: Optional[float] = None) -> Dict:
        """
        Detect sharp money movement.
        
        Args:
            opening_line: Opening spread
            current_line: Current spread
            bet_percentage: Percentage of bets on favorite (optional)
            
        Returns:
            Dict with sharp money indicators
        """
        line_movement = current_line - opening_line
        reverse_line_movement = False
        
        # Reverse line movement: line moves against public betting
        if bet_percentage is not None:
            if bet_percentage > 65 and line_movement < 0:  # Public on favorite, line moves toward dog
                reverse_line_movement = True
            elif bet_percentage < 35 and line_movement > 0:  # Public on dog, line moves toward favorite
                reverse_line_movement = True
        
        sharp_indicator = "SHARP" if reverse_line_movement else "NEUTRAL"
        
        analysis = {
            'opening_line': opening_line,
            'current_line': current_line,
            'line_movement': line_movement,
            'reverse_line_movement': reverse_line_movement,
            'sharp_indicator': sharp_indicator
        }
        
        if reverse_line_movement:
            logger.warning(f"Sharp money detected: Line moved {line_movement:+.1f} against public")
        
        return analysis
