"""
Main NFL prediction engine orchestrating all components.
"""

from datetime import datetime
from typing import Dict, Optional
import numpy as np

from .data_loader import NFLDataLoader
from .epa_analyzer import EPAAnalyzer
from .betting_analyzer import BettingAnalyzer
from database import PredictionsDB
from config import BettingConfig, InjuryConfig, TeamsConfig, EPAConfig, TravelConfig
from utils.validators import validate_team, are_division_rivals
from utils.travel import compute_travel_penalty, compute_fan_noise_boost
from logger import get_logger

logger = get_logger(__name__)


class NFLPredictor:
    """Main prediction engine combining EPA, betting analysis, and contextual factors."""
    
    def __init__(self, season: Optional[int] = None, use_database: bool = True):
        """
        Initialize NFL predictor.
        
        Args:
            season: NFL season (auto-detected if None)
            use_database: Whether to save predictions to database
        """
        self.data_loader = NFLDataLoader(season=season)
        self.epa_analyzer = EPAAnalyzer()
        self.betting_analyzer = BettingAnalyzer()
        self.db = PredictionsDB() if use_database else None
        
        logger.info(f"NFL Predictor initialized for {self.data_loader.season} season")
    
    def predict_game(self, home_team: str, away_team: str, 
                     injuries: Optional[Dict] = None,
                     weather: Optional[Dict] = None,
                     rest_days: Optional[Dict] = None,
                     odds: int = -110,
                     bankroll: float = 10000,
                     save_to_db: bool = True) -> Dict:
        """
        Generate complete game prediction.
        
        Args:
            home_team: Home team abbreviation (e.g., 'DEN')
            away_team: Away team abbreviation (e.g., 'BUF')
            injuries: Dict with injury impacts {team: impact_epa}
            weather: Dict with weather conditions
            rest_days: Dict with rest days {home: days, away: days}
            odds: American odds for betting
            bankroll: Bankroll for Kelly calculation
            save_to_db: Whether to save prediction to database
            
        Returns:
            Complete prediction dictionary
        """
        logger.info(f"\n{'='*80}\nPREDICTION: {away_team} @ {home_team}\n{'='*80}")
        
        # Validate inputs
        validate_team(home_team)
        validate_team(away_team)
        
        # Load data
        pbp = self.data_loader.load_play_by_play()
        
        # Get team plays
        home_off, home_def = self.data_loader.get_team_plays(home_team, pbp)
        away_off, away_def = self.data_loader.get_team_plays(away_team, pbp)
        
        # Calculate base EPA
        home_epa = self.epa_analyzer.calculate_team_epa(home_off, home_def)
        away_epa = self.epa_analyzer.calculate_team_epa(away_off, away_def)
        
        logger.info(f"{home_team} EPA: {home_epa['total_epa']:+.3f} | {away_team} EPA: {away_epa['total_epa']:+.3f}")
        
        # Calculate recent form
        home_recent = self.data_loader.get_recent_games(home_team, EPAConfig.RECENT_GAMES, pbp)
        away_recent = self.data_loader.get_recent_games(away_team, EPAConfig.RECENT_GAMES, pbp)
        
        home_recent_epa = self.epa_analyzer.calculate_recent_form(home_team, home_recent)
        away_recent_epa = self.epa_analyzer.calculate_recent_form(away_team, away_recent)
        
        # Combine full season + recent form
        home_combined = self.epa_analyzer.combine_full_and_recent(home_epa, home_recent_epa)
        away_combined = self.epa_analyzer.combine_full_and_recent(away_epa, away_recent_epa)
        
        # Situational stats
        home_situational = self.epa_analyzer.calculate_situational_stats(home_off, home_def)
        away_situational = self.epa_analyzer.calculate_situational_stats(away_off, away_def)
        
        # Start with combined EPA
        home_total_epa = home_combined['combined_total_epa']
        away_total_epa = away_combined['combined_total_epa']
        
        # Base EPA differential (for EPA-dominant clamp)
        base_epa_diff = home_total_epa - away_total_epa
        
        adjustments = {}
        
        # Home field advantage
        home_field_epa = BettingConfig.HOME_FIELD_EPA
        home_total_epa += home_field_epa
        adjustments['home_field'] = home_field_epa
        logger.info(f"Home field advantage: +{home_field_epa:.3f} EPA")
        
        # Altitude advantage (Denver)
        if home_team in TeamsConfig.ALTITUDE_TEAMS:
            altitude_boost = BettingConfig.ALTITUDE_ADVANTAGE_EPA
            home_total_epa += altitude_boost
            adjustments['altitude'] = altitude_boost
            logger.info(f"Altitude advantage: +{altitude_boost:.3f} EPA")
        
        # Fan noise (home boost)
        raw_fan_noise = compute_fan_noise_boost(home_team)
        fan_noise = min(raw_fan_noise, EPAConfig.CAP_FAN_NOISE_EPA)
        home_total_epa += fan_noise
        adjustments['fan_noise'] = fan_noise
        logger.info(f"Fan noise boost: +{fan_noise:.3f} EPA (raw {raw_fan_noise:+.3f})")
        
        # Travel penalty (applies to away team)
        away_rest = rest_days.get('away', None) if rest_days else None
        travel_pen = compute_travel_penalty(home_team, away_team, away_rest)
        if travel_pen != 0:
            applied_travel = travel_pen if travel_pen >= 0 else max(travel_pen, TravelConfig.MAX_PENALTY_EPA)
            away_total_epa += applied_travel
            adjustments['travel_penalty'] = applied_travel
            logger.info(f"Travel penalty (away): {applied_travel:+.3f} EPA (raw {travel_pen:+.3f})")
        
        # Division rivalry compression
        is_division = are_division_rivals(home_team, away_team)
        if is_division:
            raw_diff = home_total_epa - away_total_epa
            adjusted_diff = self.epa_analyzer.apply_division_rivalry(raw_diff, True)
            compression = raw_diff - adjusted_diff
            home_total_epa -= compression / 2
            away_total_epa += compression / 2
            adjustments['division_rivalry'] = -compression
            logger.info(f"Division rivalry: {BettingConfig.DIVISION_RIVALRY_COMPRESSION:.0%} compression")
        
        # Rest differential
        if rest_days:
            rest_diff = rest_days.get('home', 0) - rest_days.get('away', 0)
            if rest_diff != 0:
                rest_adjustment = rest_diff * 0.005  # 0.5% per day
                # Cap
                if rest_adjustment > 0:
                    rest_adjustment = min(rest_adjustment, EPAConfig.CAP_REST_EPA)
                else:
                    rest_adjustment = max(rest_adjustment, -EPAConfig.CAP_REST_EPA)
                home_total_epa += rest_adjustment
                adjustments['rest_differential'] = rest_adjustment
                logger.info(f"Rest differential: {rest_diff} days → {rest_adjustment:+.3f} EPA")
        
        # Injuries
        injury_impact = 0.0
        if injuries:
            if home_team in injuries:
                home_injury_impact = injuries[home_team]
                # Cap per-team
                home_injury_impact = max(min(home_injury_impact, EPAConfig.CAP_INJURY_PER_TEAM_EPA), -EPAConfig.CAP_INJURY_PER_TEAM_EPA)
                home_total_epa += home_injury_impact
                injury_impact += home_injury_impact
                logger.info(f"{home_team} injuries: {home_injury_impact:+.3f} EPA (capped)")
            
            if away_team in injuries:
                away_injury_impact = injuries[away_team]
                away_injury_impact = max(min(away_injury_impact, EPAConfig.CAP_INJURY_PER_TEAM_EPA), -EPAConfig.CAP_INJURY_PER_TEAM_EPA)
                away_total_epa += away_injury_impact
                injury_impact += away_injury_impact
                logger.info(f"{away_team} injuries: {away_injury_impact:+.3f} EPA (capped)")
        
        adjustments['injuries'] = injury_impact
        
        # Weather (cold, wind, rain/snow)
        weather_impact = 0.0
        if weather:
            temp = weather.get('temperature', 70)
            wind = weather.get('wind_speed', 0)
            precip = weather.get('precipitation', 0)
            
            # Cold weather slightly favors defense
            if temp < 32:
                weather_impact -= 0.01
            
            # Wind impacts passing game
            if wind > 15:
                weather_impact -= 0.015
            
            # Precipitation
            if precip > 0:
                weather_impact -= 0.01
            
            if weather_impact != 0:
                # Cap overall abs impact
                if weather_impact > 0:
                    weather_impact = min(weather_impact, EPAConfig.CAP_WEATHER_EPA)
                else:
                    weather_impact = max(weather_impact, -EPAConfig.CAP_WEATHER_EPA)
                home_total_epa += weather_impact / 2
                away_total_epa += weather_impact / 2
                adjustments['weather'] = weather_impact
                logger.info(f"Weather impact: {weather_impact:+.3f} EPA (split)")
        
        # Calculate final EPA differential
        raw_epa_differential = home_total_epa - away_total_epa

        # EPA-dominant global cap on non-EPA adjustments
        if EPAConfig.EPA_DOMINANT_MODE:
            non_epa_effect = raw_epa_differential - base_epa_diff
            cap = EPAConfig.GLOBAL_NON_EPA_CAP
            if abs(non_epa_effect) > cap:
                clamped_effect = cap if non_epa_effect > 0 else -cap
                epa_differential = base_epa_diff + clamped_effect
                adjustments['global_non_epa_cap_applied'] = float(non_epa_effect - clamped_effect)
                logger.info(f"Global non-EPA cap applied: adjusted by {non_epa_effect - clamped_effect:+.3f} EPA")
            else:
                epa_differential = raw_epa_differential
                adjustments['global_non_epa_cap_applied'] = 0.0
        else:
            epa_differential = raw_epa_differential
        
        # Convert EPA to point spread
        # Rule of thumb: 0.10 EPA ≈ 2.5 points
        predicted_spread = epa_differential / 0.04  # More aggressive conversion
        
        # Convert spread to win probability
        # Using logistic regression: P(win) = 1 / (1 + exp(-0.25 * spread))
        win_probability = 1 / (1 + np.exp(-0.25 * predicted_spread))
        
        # Determine winner
        if predicted_spread > 0:
            predicted_winner = home_team
            confidence = "HIGH" if abs(predicted_spread) > 7 else "MEDIUM" if abs(predicted_spread) > 3 else "LOW"
        else:
            predicted_winner = away_team
            confidence = "HIGH" if abs(predicted_spread) > 7 else "MEDIUM" if abs(predicted_spread) > 3 else "LOW"
        
        logger.info(f"\nPrediction: {predicted_winner} by {abs(predicted_spread):.1f}")
        logger.info(f"Win probability: {win_probability:.1%}")
        logger.info(f"Confidence: {confidence}")
        
        # Betting analysis
        betting_rec = self.betting_analyzer.calculate_betting_recommendation(
            win_probability, predicted_spread, odds, bankroll
        )
        
        # Build prediction result
        prediction = {
            'game_date': datetime.now(),
            'home_team': home_team,
            'away_team': away_team,
            'predicted_winner': predicted_winner,
            'win_probability': win_probability,
            'predicted_spread': predicted_spread,
            'confidence_level': confidence,
            
            # EPA breakdown
            'epa_differential': epa_differential,
            'home_epa': home_total_epa,
            'away_epa': away_total_epa,
            'home_base_epa': home_combined['combined_total_epa'],
            'away_base_epa': away_combined['combined_total_epa'],
            
            # Adjustments
            'adjustments': adjustments,
            'injury_impact': injury_impact,
            'weather_impact': weather_impact,
            
            # Situational stats
            'home_situational': home_situational,
            'away_situational': away_situational,
            
            # Betting
            'betting_recommendation': betting_rec,
            'sharp_money_indicator': 'NEUTRAL',  # Would need live odds data
            
            # Metadata
            'is_division_game': is_division,
            'generated_at': datetime.now().isoformat()
        }
        
        # Save to database
        if save_to_db and self.db:
            try:
                prediction_id = self.db.save_prediction(prediction)
                prediction['prediction_id'] = prediction_id
                logger.info(f"Saved prediction to database (ID: {prediction_id})")
            except Exception as e:
                logger.error(f"Failed to save prediction: {e}")
        
        return prediction
    
    def format_prediction_output(self, prediction: Dict) -> str:
        """Format prediction for display."""
        lines = [
            f"\n{'='*80}",
            f"NFL PLAYOFF PREDICTOR - {prediction['away_team']} @ {prediction['home_team']}",
            f"{'='*80}\n",
            f"🏆 PREDICTION: {prediction['predicted_winner']} wins",
            f"📊 Win Probability: {prediction['win_probability']:.1%}",
            f"📈 Spread: {prediction['predicted_winner']} {abs(prediction['predicted_spread']):.1f}",
            f"⭐ Confidence: {prediction['confidence_level']}\n",
            f"EPA Analysis:",
            f"  {prediction['home_team']}: {prediction['home_epa']:+.3f}",
            f"  {prediction['away_team']}: {prediction['away_epa']:+.3f}",
            f"  Differential: {prediction['epa_differential']:+.3f}\n",
        ]
        
        # Betting recommendation
        bet = prediction['betting_recommendation']
        lines.extend([
            f"💰 Betting Recommendation:",
            f"  Action: {bet['recommendation']}",
            f"  Kelly Bet: ${bet['fractional_kelly_amount']:.2f} ({bet['fractional_kelly_pct']:.1%})",
            f"  Edge: {bet['edge']:+.2%}",
            f"  Expected ROI: {bet['expected_roi']:+.1f}%\n",
        ])
        
        lines.append(f"{'='*80}\n")
        
        return '\n'.join(lines)
