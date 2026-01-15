"""
Automated Betting Signal Generator
Compares model predictions vs market lines and generates actionable bet recommendations.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from config import BettingConfig, KickerConfig, MarketConfig
from logger import get_logger

logger = get_logger(__name__)


class BetSignal(Enum):
    """Bet signal strength"""
    STRONG_BET = "STRONG BET"
    MEDIUM_BET = "MEDIUM BET"
    LEAN = "LEAN"
    AVOID = "AVOID"
    NO_PLAY = "NO PLAY"


@dataclass
class BettingRecommendation:
    """Single betting recommendation"""
    game: str
    game_date: str  # Game date (e.g. 'Jan 18, 2026')
    recommended_side: str
    signal: BetSignal
    model_spread: float
    market_spread: float
    edge_points: float
    edge_percent: float
    kelly_fraction: float
    suggested_units: float
    confidence: str
    reasoning: List[str]
    warnings: List[str]
    
    def __str__(self) -> str:
        return (
            f"\n{'='*80}\n"
            f"🎯 {self.signal.value}: {self.recommended_side}\n"
            f"{'='*80}\n"
            f"Game: {self.game}\n"
            f"Model Line: {self.model_spread:+.1f}\n"
            f"Market Line: {self.market_spread:+.1f}\n"
            f"Edge: {self.edge_points:+.1f} pts ({self.edge_percent:+.1%})\n"
            f"Confidence: {self.confidence}\n"
            f"Suggested Units: {self.suggested_units:.1f}\n"
            f"\nReasoning:\n" + "\n".join(f"  ✓ {r}" for r in self.reasoning) +
            (f"\n\n⚠️  Warnings:\n" + "\n".join(f"  • {w}" for w in self.warnings) if self.warnings else "")
        )


class BettingSignalGenerator:
    """
    Generates betting recommendations by comparing model predictions to market lines.
    """
    
    def __init__(self, bankroll: float = BettingConfig.DEFAULT_BANKROLL):
        self.bankroll = bankroll
        self.logger = get_logger(self.__class__.__name__)
        
    def generate_recommendation(
        self,
        game: str,
        home_team: str,
        away_team: str,
        model_prediction: Dict,
        market_spread: float,
        market_odds: int = -110,
        is_playoff: bool = False,
        game_date: str = "TBD"
    ) -> BettingRecommendation:
        """
        Generate betting recommendation for a single game.
        
        Args:
            game: Game identifier (e.g., "BAL @ KC")
            home_team: Home team abbrev
            away_team: Away team abbrev
            model_prediction: Full prediction dict from predictor
            market_spread: Current market spread (positive = home favored)
            market_odds: American odds (default -110)
            is_playoff: Whether this is a playoff game
            game_date: Game date string (e.g. 'Jan 18, 2026')
            
        Returns:
            BettingRecommendation object
        """
        # Validate required prediction fields
        model_spread = model_prediction.get('predicted_spread')
        model_prob = model_prediction.get('win_probability')
        
        if model_spread is None or model_prob is None:
            raise ValueError(
                f"Invalid prediction for {game}: missing required fields. "
                f"Got: predicted_spread={model_spread}, win_probability={model_prob}"
            )
        
        # Calculate edge
        edge_points = abs(model_spread - market_spread)
        # Avoid division by zero for pick'em games
        if abs(market_spread) > 0.01:
            edge_percent = edge_points / abs(market_spread)
        else:
            edge_percent = edge_points * 100  # For pick'em, show absolute edge
        
        # Determine recommended side
        if model_spread > market_spread:
            # Model likes home more than market
            recommended_side = f"{home_team} {market_spread:+.1f}"
        else:
            # Model likes away more than market
            recommended_side = f"{away_team} {-market_spread:+.1f}"
        
        # Generate signal based on edge and confidence
        model_confidence = model_prediction.get('confidence_level', 'MEDIUM')
        signal = self._determine_signal(
            edge_points=edge_points,
            model_confidence=model_confidence,
            market_spread=market_spread,
            is_playoff=is_playoff
        )
        
        # Calculate Kelly sizing
        kelly_fraction = self._calculate_kelly(
            model_prob=model_prob,
            market_odds=market_odds,
            edge_points=edge_points,
            market_spread=market_spread
        )
        
        suggested_units = (kelly_fraction * self.bankroll) / 100
        
        # Build reasoning
        reasoning = self._build_reasoning(
            model_prediction=model_prediction,
            edge_points=edge_points,
            is_playoff=is_playoff
        )
        
        # Build warnings
        warnings = self._build_warnings(
            edge_points=edge_points,
            market_spread=market_spread,
            model_prediction=model_prediction
        )
        
        return BettingRecommendation(
            game=game,
            game_date=game_date,
            recommended_side=recommended_side,
            signal=signal,
            model_spread=model_spread,
            market_spread=market_spread,
            edge_points=edge_points,
            edge_percent=edge_percent,
            kelly_fraction=kelly_fraction,
            suggested_units=suggested_units,
            confidence=model_confidence,
            reasoning=reasoning,
            warnings=warnings
        )
    
    def _determine_signal(
        self,
        edge_points: float,
        model_confidence: str,
        market_spread: float,
        is_playoff: bool
    ) -> BetSignal:
        """Determine bet signal strength based on edge and confidence."""
        
        # Adjust thresholds for playoffs (be more conservative)
        playoff_multiplier = 1.2 if is_playoff else 1.0
        
        # Check if line crosses key numbers
        crosses_key_number = self._crosses_key_number(market_spread, edge_points)
        
        # Signal thresholds
        if edge_points >= 4.0 * playoff_multiplier and model_confidence == "HIGH":
            return BetSignal.STRONG_BET
        elif edge_points >= 3.0 * playoff_multiplier and model_confidence in ["HIGH", "MEDIUM"]:
            return BetSignal.STRONG_BET
        elif edge_points >= 2.5 * playoff_multiplier:
            return BetSignal.MEDIUM_BET
        elif edge_points >= 1.5 * playoff_multiplier and not crosses_key_number:
            return BetSignal.LEAN
        elif edge_points >= 1.0:
            return BetSignal.LEAN
        else:
            return BetSignal.NO_PLAY
    
    def _crosses_key_number(self, market_spread: float, edge_points: float) -> bool:
        """Check if the edge crosses a key number (3, 7)."""
        key_numbers = BettingConfig.KEY_NUMBERS[:2]  # Focus on 3 and 7
        
        for key in key_numbers:
            if abs(market_spread) <= key <= abs(market_spread) + edge_points:
                return True
            if abs(market_spread) >= key >= abs(market_spread) - edge_points:
                return True
        return False
    
    def _calculate_kelly(
        self,
        model_prob: float,
        market_odds: int,
        edge_points: float,
        market_spread: float
    ) -> float:
        """Calculate Kelly fraction for bet sizing."""
        
        # Convert American odds to decimal
        if market_odds < 0:
            decimal_odds = 1 + (100 / abs(market_odds))
        else:
            decimal_odds = 1 + (market_odds / 100)
        
        # Kelly formula: (bp - q) / b
        # where b = decimal odds - 1, p = win prob, q = 1 - p
        b = decimal_odds - 1
        p = model_prob
        q = 1 - p
        
        kelly = (b * p - q) / b
        
        # Apply fractional Kelly (quarter Kelly = safest)
        fractional_kelly = kelly * BettingConfig.KELLY_FRACTION
        
        # Reduce Kelly if betting through key numbers
        if self._crosses_key_number(market_spread, edge_points):
            fractional_kelly *= MarketConfig.REDUCE_KELLY_NEAR_KEY
        
        # Cap at max bet size
        max_kelly = BettingConfig.MAX_BET_SIZE_PCT
        fractional_kelly = min(fractional_kelly, max_kelly)
        
        # Floor at 0 (no negative bets)
        return max(0, fractional_kelly)
    
    def _build_reasoning(
        self,
        model_prediction: Dict,
        edge_points: float,
        is_playoff: bool
    ) -> List[str]:
        """Build list of reasoning points for the bet."""
        reasons = []
        
        # Edge magnitude
        if edge_points >= 4:
            reasons.append(f"Large model edge: {edge_points:.1f} points")
        elif edge_points >= 2.5:
            reasons.append(f"Solid model edge: {edge_points:.1f} points")
        else:
            reasons.append(f"Moderate edge: {edge_points:.1f} points")
        
        # EPA differential
        epa_diff = model_prediction.get('epa_differential', 0)
        if abs(epa_diff) > 0.1:
            reasons.append(f"Strong EPA advantage: {epa_diff:+.3f}")
        
        # Key adjustments
        adjustments = model_prediction.get('adjustments', {})
        
        if abs(adjustments.get('weather', 0)) > 0.015:
            reasons.append("Significant weather impact modeled")
        
        if abs(adjustments.get('injuries', 0)) > 0.02:
            reasons.append("Material injury advantage")
        
        if abs(adjustments.get('travel_penalty', 0)) > 0.01:
            reasons.append("Travel disadvantage for away team")
        
        if 'advanced_matchups' in adjustments:
            adv = adjustments['advanced_matchups']
            if abs(adv.get('home', 0)) > 0.015 or abs(adv.get('away', 0)) > 0.015:
                reasons.append("Favorable matchup dynamics")
        
        if is_playoff:
            reasons.append("Playoff game - model calibrated for postseason")
        
        return reasons
    
    def _build_warnings(
        self,
        edge_points: float,
        market_spread: float,
        model_prediction: Dict
    ) -> List[str]:
        """Build list of warnings/cautions."""
        warnings = []
        
        # Key number warnings
        if self._crosses_key_number(market_spread, edge_points):
            warnings.append("Line crosses key number (3 or 7) - reduced Kelly sizing applied")
        
        # Low confidence warning
        if model_prediction.get('confidence_level') == "LOW":
            warnings.append("Low confidence prediction - consider smaller bet or pass")
        
        # Small edge warning
        if edge_points < 2.0:
            warnings.append("Edge is marginal - only bet if you trust model calibration")
        
        # Injury uncertainty
        injury_impact = model_prediction.get('injury_impact', 0)
        if abs(injury_impact) > 0.025:
            warnings.append("Significant injury impact - monitor injury reports before kickoff")
        
        # Weather uncertainty
        weather_impact = model_prediction.get('weather_impact', 0)
        if abs(weather_impact) > 0.02:
            warnings.append("Weather-dependent - check forecast closer to game time")
        
        return warnings
    
    def generate_weekly_card(
        self,
        predictions: List[Dict],
        market_lines: Dict[str, float],
        is_playoff: bool = False
    ) -> List[BettingRecommendation]:
        """
        Generate full weekly betting card with all recommendations.
        
        Args:
            predictions: List of model prediction dicts
            market_lines: Dict mapping "AWAY @ HOME" to spread (positive = home favored)
            is_playoff: Whether these are playoff games
            
        Returns:
            List of BettingRecommendation objects, sorted by signal strength
        """
        recommendations = []
        
        for pred in predictions:
            game_key = f"{pred['away_team']} @ {pred['home_team']}"
            
            if game_key not in market_lines:
                self.logger.warning(f"No market line found for {game_key}")
                continue
            
            # Extract game date from prediction if available
            game_date = pred.get('game_date', 'TBD')
            
            rec = self.generate_recommendation(
                game=game_key,
                home_team=pred['home_team'],
                away_team=pred['away_team'],
                model_prediction=pred,
                market_spread=market_lines[game_key],
                is_playoff=is_playoff,
                game_date=game_date
            )
            
            recommendations.append(rec)
        
        # Sort by signal strength then edge
        signal_order = {
            BetSignal.STRONG_BET: 0,
            BetSignal.MEDIUM_BET: 1,
            BetSignal.LEAN: 2,
            BetSignal.NO_PLAY: 3,
            BetSignal.AVOID: 4
        }
        
        recommendations.sort(
            key=lambda x: (signal_order[x.signal], -x.edge_points)
        )
        
        return recommendations
    
    def print_weekly_card(self, recommendations: List[BettingRecommendation]) -> None:
        """Print formatted weekly betting card."""
        
        print("\n" + "="*80)
        print("🏈 WEEKLY BETTING CARD 🏈")
        print("="*80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
        print(f"Bankroll: ${self.bankroll:,.0f}")
        print("="*80)
        
        # Group by signal
        by_signal = {}
        for rec in recommendations:
            if rec.signal not in by_signal:
                by_signal[rec.signal] = []
            by_signal[rec.signal].append(rec)
        
        # Print each group
        for signal in [BetSignal.STRONG_BET, BetSignal.MEDIUM_BET, BetSignal.LEAN, BetSignal.NO_PLAY]:
            if signal in by_signal:
                print(f"\n{'='*80}")
                print(f"{signal.value} ({len(by_signal[signal])} games)")
                print(f"{'='*80}")
                
                for rec in by_signal[signal]:
                    print(rec)
        
        # Summary
        strong_bets = [r for r in recommendations if r.signal == BetSignal.STRONG_BET]
        total_units = sum(r.suggested_units for r in strong_bets)
        
        print(f"\n{'='*80}")
        print(f"📊 SUMMARY")
        print(f"{'='*80}")
        print(f"Strong Bets: {len(strong_bets)}")
        print(f"Total Suggested Units: {total_units:.1f}")
        print(f"Total Risk: ${total_units * 100:,.0f} ({total_units * 100 / self.bankroll:.1%} of bankroll)")
        print(f"{'='*80}\n")
