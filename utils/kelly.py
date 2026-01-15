"""Kelly Criterion bet sizing calculator."""

from typing import Dict
from config import BettingConfig
from logger import get_logger

logger = get_logger(__name__)


class KellyCalculator:
    """Calculate optimal bet sizes using Kelly Criterion."""
    
    @staticmethod
    def american_to_decimal(odds: int) -> float:
        """
        Convert American odds to decimal odds.
        
        Args:
            odds: American odds (e.g., -110, +150)
            
        Returns:
            Decimal odds
        """
        if odds > 0:
            return (odds / 100) + 1
        else:
            return (100 / abs(odds)) + 1
    
    @staticmethod
    def calculate_implied_prob(odds: int) -> float:
        """
        Calculate implied probability from American odds.
        
        Args:
            odds: American odds
            
        Returns:
            Implied probability (0-1)
        """
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)
    
    @staticmethod
    def full_kelly(win_prob: float, odds: int) -> float:
        """
        Calculate full Kelly fraction.
        
        Args:
            win_prob: Win probability (0-1)
            odds: American odds
            
        Returns:
            Kelly fraction (0-1)
        """
        decimal_odds = KellyCalculator.american_to_decimal(odds)
        b = decimal_odds - 1  # Net odds
        p = win_prob
        q = 1 - p
        
        kelly = (b * p - q) / b
        
        return max(0, kelly)  # Never negative
    
    @staticmethod
    def calculate_bet_size(win_prob: float, odds: int, bankroll: float, 
                          fraction: float = None) -> Dict:
        """
        Calculate recommended bet size.
        
        Args:
            win_prob: Win probability (0-1)
            odds: American odds
            bankroll: Total bankroll
            fraction: Kelly fraction to use (default from config)
            
        Returns:
            Dict with bet sizing recommendations
        """
        if fraction is None:
            fraction = BettingConfig.KELLY_FRACTION
        
        full_kelly_pct = KellyCalculator.full_kelly(win_prob, odds)
        implied_prob = KellyCalculator.calculate_implied_prob(odds)
        edge = win_prob - implied_prob
        
        # Apply fraction (typically 0.25 or 0.5 for safety)
        fractional_kelly_pct = full_kelly_pct * fraction
        
        # Calculate dollar amounts
        full_kelly_amount = bankroll * full_kelly_pct
        fractional_kelly_amount = bankroll * fractional_kelly_pct
        
        # Expected value
        decimal_odds = KellyCalculator.american_to_decimal(odds)
        ev = (win_prob * decimal_odds * fractional_kelly_amount) - fractional_kelly_amount
        roi = (ev / fractional_kelly_amount * 100) if fractional_kelly_amount > 0 else 0
        
        recommendation = {
            'full_kelly_pct': full_kelly_pct,
            'full_kelly_amount': full_kelly_amount,
            'fractional_kelly_pct': fractional_kelly_pct,
            'fractional_kelly_amount': fractional_kelly_amount,
            'kelly_fraction_used': fraction,
            'edge': edge,
            'implied_prob': implied_prob,
            'expected_value': ev,
            'expected_roi': roi,
            'bankroll': bankroll
        }
        
        # Determine if bet is +EV
        if edge > 0:
            recommendation['recommendation'] = 'BET'
            recommendation['confidence'] = 'HIGH' if edge > 0.10 else 'MEDIUM' if edge > 0.05 else 'LOW'
        else:
            recommendation['recommendation'] = 'PASS'
            recommendation['confidence'] = 'NEGATIVE_EV'
        
        logger.debug(f"Kelly: {fractional_kelly_pct:.2%} of bankroll = ${fractional_kelly_amount:.2f} (Edge: {edge:+.2%})")
        
        return recommendation
