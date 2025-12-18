# NFL Playoff Predictor

AI-powered NFL playoff analysis using advanced EPA (Expected Points Added) metrics to predict matchups and provide betting insights based on team efficiency rather than traditional stats.

## Features

- 📊 **EPA-based analysis**: Uses Expected Points Added instead of misleading volume stats
- 🏈 **Playoff team rankings**: Ranks teams by offensive and defensive efficiency
- ⚔️ **Matchup predictions**: AI-powered analysis of head-to-head matchups
- 💰 **Betting insights**: Data-driven recommendations for better betting decisions
- 📈 **Visual comparisons**: See how teams stack up against each other
- 🎯 **Win probability**: Estimates based on efficiency metrics, not just records

## Why EPA Matters

Traditional stats like total yards and points can be misleading:
- **Garbage time** inflates stats when games are already decided
- **Volume stats** don't account for efficiency
- **Win-loss records** don't show how teams actually perform

**EPA (Expected Points Added)** measures:
- Points added per play based on field position, down, and distance
- Offensive efficiency (points created per play)
- Defensive efficiency (points prevented per play)
- True team strength regardless of schedule or garbage time

## Prerequisites

- Python 3.7+
- Azure OpenAI API access
- Internet connection (to fetch NFL data)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/james-no/nfl-playoff-predictor.git
   cd nfl-playoff-predictor
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API key**
   
   Create a `.env` file:
   ```
   AZURE_API_KEY=your_api_key_here
   ```

## Usage

### Basic Analysis

```bash
python3 nfl_predictor.py
```

This will:
1. Fetch current season EPA data
2. Show playoff team rankings
3. Let you analyze specific matchups

### Example Session

```
=== NFL Playoff Predictor ===
Fetching 2024 NFL data...

📊 Top 5 Offenses by EPA/play:
1. Buffalo Bills: 0.145
2. Kansas City Chiefs: 0.132
3. Baltimore Ravens: 0.128
4. Detroit Lions: 0.121
5. San Francisco 49ers: 0.115

🛡️ Top 5 Defenses by EPA/play:
1. San Francisco 49ers: -0.098
2. Baltimore Ravens: -0.089
3. Cleveland Browns: -0.081
4. Dallas Cowboys: -0.075
5. Buffalo Bills: -0.072

Enter matchup (e.g., 'Chiefs vs Bills') or 'quit': Chiefs vs Bills

🤔 Analyzing matchup...

Matchup Analysis: Kansas City Chiefs vs Buffalo Bills

Offensive Comparison:
- Bills have a significant offensive advantage (0.145 vs 0.132 EPA/play)
- Bills passing game is more efficient
- Chiefs rushing attack is slightly better

Defensive Comparison:
- Bills defense is stronger (-0.072 vs -0.055 EPA/play)
- Bills better against the pass
- Chiefs better against the run

Key Factors:
- Home field advantage matters in playoffs
- Bills have edge in both offense and defense
- Chiefs have playoff experience advantage

Prediction: Bills 55% win probability in neutral site
Betting Insight: Bills slight favorites, value depends on spread

Enter matchup or 'quit':
```

## How It Works

### 1. Data Collection

Uses `nfl_data_py` library to fetch play-by-play data with EPA calculations:

```python
import nfl_data_py as nfl

# Get current season data
pbp = nfl.import_pbp_data([2024])

# Filter to regular plays
pbp = pbp[(pbp['rush'] == 1) | (pbp['pass'] == 1)]
```

### 2. EPA Calculation

Calculates offensive and defensive EPA per play for each team:

```python
# Offensive EPA
offense = pbp.groupby('posteam')['epa'].mean()

# Defensive EPA (negative is better)
defense = pbp.groupby('defteam')['epa'].mean()
```

### 3. AI Analysis

Sends team stats to GPT-4 for intelligent matchup analysis:

```python
prompt = f"""
Analyze this NFL playoff matchup:

Team A Offense EPA: {team_a_off}
Team A Defense EPA: {team_a_def}
Team B Offense EPA: {team_b_off}
Team B Defense EPA: {team_b_def}

Provide:
1. Win probability estimate
2. Key factors in the matchup
3. Betting insight
"""
```

## Understanding EPA

**Positive EPA (Offense)**: Team adds points
- 0.15+ : Elite offense
- 0.10-0.15: Great offense
- 0.05-0.10: Good offense
- 0.00-0.05: Average offense
- Below 0.00: Below average

**Negative EPA (Defense)**: Team prevents points
- Below -0.08: Elite defense
- -0.08 to -0.05: Great defense
- -0.05 to -0.02: Good defense
- -0.02 to 0.00: Average defense
- Above 0.00: Below average

## Project Structure

```
nfl-playoff-predictor/
├── .env                    # Your API key
├── requirements.txt        # Python dependencies
├── nfl_predictor.py       # Main script
├── README.md              # This file
└── .gitignore            # Ignore sensitive files
```

## Advanced Features (Optional Enhancements)

Once you have the basic version working:

- **Historical matchups**: Compare to past meetings
- **Injury reports**: Factor in key player absences
- **Weather data**: Account for weather in outdoor stadiums
- **Vegas odds comparison**: Compare AI predictions to betting lines
- **Playoff simulation**: Run thousands of bracket simulations
- **Export reports**: Generate PDF analysis reports
- **Twitter bot**: Auto-tweet predictions

## Data Sources

- **Play-by-play data**: nflfastR via nfl_data_py
- **EPA calculations**: Pre-computed by nflfastR
- **Team info**: NFL official data
- **Analysis**: Azure OpenAI GPT-4.1

## Cost Estimate

- Data fetching: FREE (nfl_data_py)
- Single matchup analysis: $0.01-0.03
- Full playoff bracket (14 teams): $0.30-0.50
- Season-long usage: $2-5

Very affordable for the insights provided!

## Responsible Gambling

This tool provides **data-driven insights**, not guarantees:
- No prediction is 100% accurate
- Upsets happen in sports
- Use for entertainment and research
- Gamble responsibly within your means
- Sports betting should never be your primary income source

## Example Insights

**Traditional thinking**: "Team A is 12-2, Team B is 9-5, bet on Team A"

**EPA thinking**: "Team A has weak EPA, inflated by blowouts. Team B has strong EPA against tough schedule. Team B is undervalued."

This is where smart money is made.

## Troubleshooting

**Data not loading**
- Check internet connection
- Verify `nfl_data_py` is installed
- Season data may not be available yet (early season)

**API errors**
- Check `.env` file has correct API key
- Verify Azure OpenAI quota
- Check API endpoint is correct

**Slow performance**
- First data load takes 30-60 seconds
- Subsequent loads are cached
- Use `max_tokens=300` to speed up responses

## Learning Outcomes

After building this project:
- ✅ Working with sports analytics data
- ✅ Understanding advanced NFL metrics
- ✅ Combining data analysis with AI
- ✅ Building practical sports betting tools
- ✅ Data visualization and presentation

## Future Enhancements

- Web interface with Flask
- Real-time odds scraping
- Machine learning models
- Player-level EPA analysis
- Live game predictions
- Historical accuracy tracking

## Related Projects

- [Code Comment Generator](https://github.com/james-no/code-comment-generator)
- [Interview Practice Bot](https://github.com/james-no/interview-practice-bot)

## Disclaimer

This tool is for **educational and entertainment purposes only**. Past performance does not guarantee future results. The predictions are based on statistical analysis and should not be considered professional gambling advice.

## License

MIT

## Author

James No - [GitHub](https://github.com/james-no)

---

**Ready to beat the bookies with data?** Install dependencies and start analyzing! 🏈📊
