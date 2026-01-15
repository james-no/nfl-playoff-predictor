## 🏗️ NFL Playoff Predictor v3.0 - Architecture Documentation

### System Overview
Professional-grade NFL betting system with object-oriented architecture, comprehensive tracking, and web UI.

### Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI LAYER                        │
│                   (streamlit_app.py)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  CORE PREDICTION ENGINE                      │
│                    (core/predictor.py)                       │
│  - Orchestrates all analysis                                 │
│  - Combines EPA + Betting + Injuries                         │
│  - Returns complete predictions                              │
└─┬────────────┬────────────┬─────────────┬───────────────────┘
  │            │            │             │
┌─▼──────┐ ┌──▼──────┐ ┌──▼────────┐ ┌──▼─────────┐
│  Data  │ │   EPA   │ │  Betting  │ │  Database  │
│ Loader │ │Analyzer │ │ Analyzer  │ │  Tracker   │
└────────┘ └─────────┘ └───────────┘ └────────────┘
     │          │             │             │
┌────▼──────────▼─────────────▼─────────────▼────────────────┐
│                    SHARED UTILITIES                          │
│  - Config Management (config.py)                             │
│  - Logging System (logger.py)                                │
│  - Kelly Calculator (utils/)                                 │
└──────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. Configuration Layer (`config.py`) ✅
**Purpose:** Centralized settings management  
**Key Classes:**
- `SeasonConfig`: Auto-detect season, data fetch settings
- `EPAConfig`: EPA weights, thresholds, situational stats
- `BettingConfig`: Home field, altitude, Kelly Criterion
- `InjuryConfig`: Position-specific injury impacts
- `DatabaseConfig`, `LoggingConfig`, `UIConfig`

**Usage:**
```python
from config import BettingConfig
home_advantage = BettingConfig.HOME_FIELD_EPA  # 0.029
```

#### 2. Logging System (`logger.py`) ✅
**Purpose:** Structured logging with rotation  
**Features:**
- Console + file logging
- Rotating file handler (10MB max, 3 backups)
- Different log levels (DEBUG file, INFO console)

**Usage:**
```python
from logger import get_logger
logger = get_logger(__name__)
logger.info("Prediction started")
logger.warning("Sharp money detected")
```

#### 3. Database Layer (`database.py`)
**Purpose:** Track predictions, CLV, performance  
**Tables:**
- `predictions`: All predictions made
- `results`: Actual game results  
- `performance`: Win rate, ROI, CLV tracking
- `bets`: User bet history

**Schema:**
```sql
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY,
    game_date DATETIME,
    home_team TEXT,
    away_team TEXT,
    predicted_winner TEXT,
    win_probability REAL,
    spread REAL,
    over_under REAL,
    created_at DATETIME
);

CREATE TABLE results (
    id INTEGER PRIMARY KEY,
    prediction_id INTEGER,
    actual_winner TEXT,
    actual_margin INTEGER,
    bet_result TEXT,  -- WIN/LOSS/PUSH
    clv REAL,  -- Closing Line Value
    FOREIGN KEY (prediction_id) REFERENCES predictions(id)
);
```

#### 4. Core Engine (`core/`)

##### 4.1 Data Loader (`core/data_loader.py`)
**Purpose:** Fetch and cache NFL data  
**Class:** `NFLDataLoader`
```python
class NFLDataLoader:
    def __init__(self, season=None):
        self.season = season or SeasonConfig.get_current_season()[0]
        self.cache = {}
        
    def load_play_by_play(self) -> pd.DataFrame:
        """Load NFL play-by-play data with caching"""
        
    def get_team_schedule(self, team: str) -> pd.DataFrame:
        """Get schedule for specific team"""
```

##### 4.2 EPA Analyzer (`core/epa_analyzer.py`)
**Purpose:** Calculate all EPA metrics  
**Class:** `EPAAnalyzer`
```python
class EPAAnalyzer:
    def calculate_team_epa(self, pbp: pd.DataFrame) -> dict:
        """Calculate offensive and defensive EPA"""
        
    def calculate_recent_form(self, pbp: pd.DataFrame, weeks=4) -> dict:
        """Calculate recent form (last N games)"""
        
    def calculate_situational_stats(self, pbp: pd.DataFrame) -> dict:
        """3rd down, red zone, 4th quarter stats"""
        
    def get_opponent_adjusted_epa(self, pbp: pd.DataFrame) -> dict:
        """Adjust for strength of schedule"""
```

##### 4.3 Betting Analyzer (`core/betting_analyzer.py`)
**Purpose:** Betting intelligence and Kelly Criterion  
**Class:** `BettingAnalyzer`
```python
class BettingAnalyzer:
    def calculate_kelly_bet_size(self, win_prob: float, odds: int, 
                                 bankroll: float) -> dict:
        """Kelly Criterion bet sizing"""
        
    def analyze_sharp_money(self, game: str) -> dict:
        """Track sharp money movement"""
        
    def check_key_numbers(self, spread: float) -> dict:
        """Analyze key number crosses"""
        
    def get_clv(self, bet_line: float, closing_line: float) -> float:
        """Calculate Closing Line Value"""
```

##### 4.4 Main Predictor (`core/predictor.py`)
**Purpose:** Orchestrate all analysis  
**Class:** `NFLPredictor`
```python
class NFLPredictor:
    def __init__(self):
        self.data_loader = NFLDataLoader()
        self.epa_analyzer = EPAAnalyzer()
        self.betting_analyzer = BettingAnalyzer()
        self.db = PredictionsDB()
        self.logger = get_logger(__name__)
        
    def predict_game(self, home_team: str, away_team: str, 
                     save_to_db: bool = True) -> dict:
        """
        Complete prediction with all factors
        
        Returns:
            {
                'winner': str,
                'win_probability': float,
                'spread': float,
                'over_under': float,
                'confidence': str,
                'kelly_bet_size': dict,
                'factors': dict  # All contributing factors
            }
        """
```

#### 5. Streamlit UI (`streamlit_app.py`)
**Purpose:** User-friendly web interface  
**Features:**
- Team selection dropdowns
- Real-time predictions
- Injury reports display
- Betting intelligence panel
- Historical performance charts
- CLV tracking visualization

**Layout:**
```
┌─────────────────────────────────────────┐
│  🏈 NFL Playoff Predictor v3.0          │
│  83.3% ATS Accuracy                     │
├─────────────┬───────────────────────────┤
│ Home Team ▼ │ Away Team ▼               │
│    DEN      │    BUF                    │
├─────────────┴───────────────────────────┤
│        [🎯 Generate Prediction]         │
├─────────────────────────────────────────┤
│ Win Prob │ Spread │ Kelly Bet          │
│  57.8%   │ BUF -6.2│   $285            │
├─────────────────────────────────────────┤
│ 📊 Injury Report                        │
│ 💰 Sharp Money Intel                    │
│ ⛰️  Environmental Factors                │
└─────────────────────────────────────────┘
```

### Data Flow

#### Prediction Flow:
```
1. User selects teams in Streamlit
   ↓
2. streamlit_app.py calls NFLPredictor.predict_game()
   ↓
3. NFLPredictor coordinates:
   - DataLoader.load_play_by_play()
   - EPAAnalyzer.calculate_team_epa()
   - BettingAnalyzer.calculate_kelly_bet_size()
   ↓
4. Combine all factors into prediction
   ↓
5. Save to database (PredictionsDB)
   ↓
6. Return results to UI
   ↓
7. Display formatted results to user
```

### Error Handling Strategy

**Graceful Degradation:**
```python
try:
    pbp = data_loader.load_play_by_play()
except APIRateLimitError:
    logger.warning("API rate limit - using cached data")
    pbp = data_loader.get_cached_data()
except NetworkError:
    logger.error("Network error - cannot fetch data")
    return {"error": "Network unavailable", "use_offline_mode": True}
```

**Fallback Chain:**
1. Try live API
2. Use cached data (if < 24h old)
3. Use historical averages
4. Return error with guidance

### Testing Strategy

#### Unit Tests (`tests/`)
```
tests/
├── test_epa_analyzer.py       # EPA calculations
├── test_betting_analyzer.py   # Kelly, CLV, key numbers
├── test_predictor.py          # End-to-end predictions
└── test_database.py           # DB operations
```

**Test Coverage Goals:**
- Core logic: 90%+
- Utility functions: 80%+
- UI: Manual testing

### Deployment

#### Local Development:
```bash
streamlit run streamlit_app.py
```

#### Production (Streamlit Cloud):
```bash
# Push to GitHub
git push origin main

# Deploy on Streamlit Cloud:
# 1. Go to share.streamlit.io
# 2. Connect GitHub repo
# 3. Set main file: streamlit_app.py
# 4. Deploy!
```

### Performance Optimization

**Caching Strategy:**
- NFL data: Cache for 24 hours
- Predictions: Cache for game day
- Static configs: In-memory cache

**Database Indexing:**
```sql
CREATE INDEX idx_game_date ON predictions(game_date);
CREATE INDEX idx_teams ON predictions(home_team, away_team);
CREATE INDEX idx_created ON predictions(created_at);
```

### Security Considerations

1. **API Keys:** Environment variables only
2. **Database:** Local SQLite (no external access)
3. **Input Validation:** All user inputs sanitized
4. **Rate Limiting:** Max 10 predictions/minute per user

### Monitoring & Metrics

**Track:**
- Prediction accuracy (straight up & ATS)
- Average CLV
- ROI over time
- API call success rate
- Error rates by type

**Dashboards:**
- Streamlit: Real-time performance
- Database: Historical trends
- Logs: Error analysis

### Future Enhancements

**Phase 4 (Post v3.0):**
- Real-time odds scraping
- Mobile app (React Native)
- Machine learning models
- Automated bet placement API
- Multi-user support with auth
- Subscription payments

### Dependencies

**Core:**
- nflreadpy: NFL data
- polars: Data processing
- pandas: Analysis
- numpy: Calculations

**Infrastructure:**
- streamlit: UI
- sqlite3: Database
- logging: Built-in

**Optional:**
- openai: AI analysis
- requests: API calls
- pytest: Testing

### File Structure Summary
```
nfl-playoff-predictor/
├── config.py              ✅ Settings
├── logger.py              ✅ Logging
├── database.py            → DB layer
├── core/
│   ├── __init__.py
│   ├── data_loader.py     → Fetch data
│   ├── epa_analyzer.py    → EPA calcs
│   ├── betting_analyzer.py→ Betting
│   └── predictor.py       → Main engine
├── utils/
│   ├── __init__.py
│   └── kelly.py           → Bet sizing
├── streamlit_app.py       → Web UI
├── tests/
│   └── test_*.py          → Unit tests
├── requirements.txt       → Dependencies
├── ARCHITECTURE.md        → This file
└── README.md              → User docs
```

### Quick Start (After Build Complete)

```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit UI
streamlit run streamlit_app.py

# Or use CLI
python -c "from core.predictor import NFLPredictor; p = NFLPredictor(); print(p.predict_game('DEN', 'BUF'))"

# Run tests
pytest tests/

# View logs
tail -f nfl_predictor.log
```

### Support & Contribution

**Issues:** GitHub Issues  
**Questions:** README.md  
**Contributions:** Pull requests welcome  

---

**Version:** 3.0  
**Last Updated:** 2026-01-15  
**Author:** James No  
**License:** MIT
