"""
Database layer for tracking predictions, results, and performance.

Provides SQLite-backed persistence for:
- Predictions made
- Actual game results
- Closing Line Value (CLV) tracking
- Performance metrics (accuracy, ROI)
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager

from config import DatabaseConfig
from logger import get_logger

logger = get_logger(__name__)


class PredictionsDB:
    """SQLite database for tracking NFL predictions and performance."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file (default from config)
        """
        self.db_path = db_path or DatabaseConfig.DB_PATH
        self.init_database()
        logger.info(f"Database initialized at {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Predictions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_date DATETIME NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    predicted_winner TEXT NOT NULL,
                    win_probability REAL NOT NULL,
                    predicted_spread REAL NOT NULL,
                    predicted_total REAL,
                    confidence_level TEXT,
                    epa_differential REAL,
                    home_epa REAL,
                    away_epa REAL,
                    injury_impact REAL,
                    weather_impact REAL,
                    sharp_money_indicator TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id INTEGER NOT NULL,
                    actual_winner TEXT NOT NULL,
                    home_score INTEGER NOT NULL,
                    away_score INTEGER NOT NULL,
                    actual_margin INTEGER NOT NULL,
                    actual_total INTEGER NOT NULL,
                    opening_spread REAL,
                    closing_spread REAL,
                    clv REAL,
                    bet_result TEXT,
                    bet_profit REAL,
                    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prediction_id) REFERENCES predictions(id)
                )
            ''')
            
            # Performance summary table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_start DATETIME NOT NULL,
                    period_end DATETIME NOT NULL,
                    total_predictions INTEGER DEFAULT 0,
                    correct_predictions INTEGER DEFAULT 0,
                    accuracy_straight_up REAL DEFAULT 0.0,
                    accuracy_ats REAL DEFAULT 0.0,
                    average_clv REAL DEFAULT 0.0,
                    total_profit REAL DEFAULT 0.0,
                    roi REAL DEFAULT 0.0,
                    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bets table (for bankroll tracking)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id INTEGER NOT NULL,
                    bet_type TEXT NOT NULL,
                    bet_amount REAL NOT NULL,
                    odds INTEGER NOT NULL,
                    kelly_fraction REAL,
                    placed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prediction_id) REFERENCES predictions(id)
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_predictions_date 
                ON predictions(game_date)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_predictions_teams 
                ON predictions(home_team, away_team)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_results_prediction 
                ON results(prediction_id)
            ''')
            
            logger.info("Database schema created/verified")
    
    def save_prediction(self, prediction: Dict) -> int:
        """
        Save a prediction to the database.
        
        Args:
            prediction: Dictionary containing prediction details
            
        Returns:
            prediction_id: ID of the saved prediction
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO predictions (
                    game_date, home_team, away_team, predicted_winner,
                    win_probability, predicted_spread, predicted_total,
                    confidence_level, epa_differential, home_epa, away_epa,
                    injury_impact, weather_impact, sharp_money_indicator
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prediction.get('game_date'),
                prediction['home_team'],
                prediction['away_team'],
                prediction['predicted_winner'],
                prediction['win_probability'],
                prediction['predicted_spread'],
                prediction.get('predicted_total'),
                prediction.get('confidence_level'),
                prediction.get('epa_differential'),
                prediction.get('home_epa'),
                prediction.get('away_epa'),
                prediction.get('injury_impact', 0.0),
                prediction.get('weather_impact', 0.0),
                prediction.get('sharp_money_indicator', 'NEUTRAL')
            ))
            
            prediction_id = cursor.lastrowid
            logger.info(f"Saved prediction {prediction_id}: {prediction['away_team']} @ {prediction['home_team']}")
            return prediction_id
    
    def save_result(self, prediction_id: int, result: Dict) -> int:
        """
        Save actual game result.
        
        Args:
            prediction_id: ID of the prediction
            result: Dictionary containing game result
            
        Returns:
            result_id: ID of the saved result
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO results (
                    prediction_id, actual_winner, home_score, away_score,
                    actual_margin, actual_total, opening_spread, closing_spread,
                    clv, bet_result, bet_profit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prediction_id,
                result['actual_winner'],
                result['home_score'],
                result['away_score'],
                result['actual_margin'],
                result['actual_total'],
                result.get('opening_spread'),
                result.get('closing_spread'),
                result.get('clv'),
                result.get('bet_result'),
                result.get('bet_profit')
            ))
            
            result_id = cursor.lastrowid
            logger.info(f"Saved result {result_id} for prediction {prediction_id}")
            return result_id
    
    def get_performance_stats(self, days: int = 30) -> Dict:
        """
        Calculate performance statistics.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with accuracy, CLV, ROI metrics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get predictions with results
            cursor.execute('''
                SELECT 
                    p.predicted_winner, p.predicted_spread, p.win_probability,
                    r.actual_winner, r.actual_margin, r.clv, r.bet_result, r.bet_profit
                FROM predictions p
                JOIN results r ON p.id = r.prediction_id
                WHERE p.game_date >= datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            rows = cursor.fetchall()
            
            if not rows:
                return {
                    'total_predictions': 0,
                    'accuracy_su': 0.0,
                    'accuracy_ats': 0.0,
                    'avg_clv': 0.0,
                    'total_profit': 0.0,
                    'roi': 0.0
                }
            
            total = len(rows)
            correct_su = sum(1 for r in rows if r['predicted_winner'] == r['actual_winner'])
            correct_ats = sum(1 for r in rows if r['bet_result'] == 'WIN')
            avg_clv = sum(r['clv'] or 0 for r in rows) / total
            total_profit = sum(r['bet_profit'] or 0 for r in rows)
            
            return {
                'total_predictions': total,
                'accuracy_su': correct_su / total if total > 0 else 0.0,
                'accuracy_ats': correct_ats / total if total > 0 else 0.0,
                'avg_clv': avg_clv,
                'total_profit': total_profit,
                'roi': (total_profit / (total * 100)) if total > 0 else 0.0  # Assuming $100 avg bet
            }
    
    def get_recent_predictions(self, limit: int = 10) -> List[Dict]:
        """
        Get recent predictions with results.
        
        Args:
            limit: Maximum number of predictions to return
            
        Returns:
            List of prediction dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    p.*, r.actual_winner, r.home_score, r.away_score, 
                    r.clv, r.bet_result
                FROM predictions p
                LEFT JOIN results r ON p.id = r.prediction_id
                ORDER BY p.game_date DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def calculate_clv(self, prediction_id: int, closing_spread: float) -> Optional[float]:
        """
        Calculate Closing Line Value for a prediction.
        
        Args:
            prediction_id: ID of the prediction
            closing_spread: The closing line spread
            
        Returns:
            CLV in points (positive = beat the closing line)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT predicted_spread FROM predictions WHERE id = ?
            ''', (prediction_id,))
            
            row = cursor.fetchone()
            if row:
                predicted_spread = row['predicted_spread']
                clv = abs(predicted_spread) - abs(closing_spread)
                logger.debug(f"CLV for prediction {prediction_id}: {clv:.2f}")
                return clv
            
            return None
    
    def save_bet(self, prediction_id: int, bet_type: str, amount: float, 
                 odds: int, kelly_fraction: float = None) -> int:
        """
        Record a bet placed.
        
        Args:
            prediction_id: ID of the prediction
            bet_type: Type of bet (SPREAD, ML, TOTAL)
            amount: Bet amount in dollars
            odds: American odds
            kelly_fraction: Kelly fraction used
            
        Returns:
            bet_id: ID of the saved bet
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bets (prediction_id, bet_type, bet_amount, odds, kelly_fraction)
                VALUES (?, ?, ?, ?, ?)
            ''', (prediction_id, bet_type, amount, odds, kelly_fraction))
            
            bet_id = cursor.lastrowid
            logger.info(f"Saved bet {bet_id}: ${amount} on prediction {prediction_id}")
            return bet_id
