# Weekly Betting Card Guide

## Overview
The betting card system automatically tells you **what to bet, how much, and why** by comparing your model's predictions to current market lines.

## How to Use (Week-by-Week)

### Step 1: Get Current Market Lines
Before each week of games, update the lines in `weekly_betting_card.py`:

```python
def get_divisional_round_lines():
    return {
        "HOU @ KC": 8.5,      # Update this number
        "WAS @ DET": 9.0,     # from VegasInsider
        "LA @ PHI": 6.0,      # or Pro-Football-Reference
        "BAL @ BUF": 1.5,
    }
```

**Where to get lines:**
- ✅ **VegasInsider.com** (free, unbiased)
- ✅ **Pro-Football-Reference.com** (closing lines archive)
- ✅ **The Action Network** (real-time line movement)
- ✅ **Covers.com** (consensus lines)
- ❌ Avoid ESPN/NY Post (biased)

### Step 2: Update Weather Forecasts
Update the weather dict for each game (check 24-48 hours before kickoff):

```python
weather={
    'temperature': 35,  # Degrees F
    'wind_speed': 10,   # MPH
    'precipitation': 0  # 0=none, 1=rain/snow
}
```

### Step 3: Run the Script
```bash
python weekly_betting_card.py
```

### Step 4: Review Output

The script generates a betting card that looks like this:

```
================================================================================
🎯 STRONG BET: BAL +1.5
================================================================================
Game: BAL @ BUF
Model Line: -0.5
Market Line: +1.5
Edge: +2.0 pts (+133%)
Confidence: HIGH
Suggested Units: 2.5

Reasoning:
  ✓ Solid model edge: 2.0 points
  ✓ Strong EPA advantage: +0.085
  ✓ Favorable matchup dynamics

⚠️  Warnings:
  • Line crosses key number (3 or 7) - reduced Kelly sizing applied
```

## Understanding the Signals

### 🔥 STRONG BET
- **Edge:** 3+ points vs market
- **Action:** BET THIS
- **Unit Sizing:** Follow suggested units (typically 2-4 units)
- **Confidence:** High model confidence + large edge

### 📊 MEDIUM BET
- **Edge:** 2.5-3 points vs market
- **Action:** Strong consideration, smaller size
- **Unit Sizing:** 1-2 units
- **Confidence:** Good edge but needs verification

### 👀 LEAN
- **Edge:** 1.5-2.5 points vs market
- **Action:** Optional / parlay leg only
- **Unit Sizing:** 0.5-1 unit
- **Confidence:** Model likes it slightly, but marginal

### ❌ NO PLAY
- **Edge:** <1.5 points
- **Action:** DO NOT BET
- **Reason:** Edge too small to overcome juice

## Unit Sizing & Kelly Criterion

The system uses **Quarter Kelly** (safest approach):
- 1 unit = $100 (for $10k bankroll)
- 2.5 units = $250 bet
- Max bet = 5% of bankroll

**Example with $10k bankroll:**
```
Strong Bet: 3.2 units = $320
Medium Bet: 1.5 units = $150
Lean: 0.8 units = $80
```

## What the System Does Automatically

✅ **Compares model spread to market spread**
- Finds where your model disagrees with Vegas by 2+ points

✅ **Adjusts for key numbers**
- Reduces bet size when line crosses 3 or 7

✅ **Applies Kelly sizing**
- Calculates optimal bet size based on edge

✅ **Flags warnings**
- Injury-dependent bets
- Weather-dependent bets  
- Low confidence predictions

✅ **Exports to CSV**
- Tracks all recommendations for performance analysis

## Weekly Workflow

### Regular Season (17 weeks)
Run every **Tuesday evening** after lines are posted:
1. Update lines (Tuesday opening lines)
2. Run script
3. Track line movement Wed-Sat
4. Bet Thursday if line moves in your favor
5. Otherwise bet Sunday morning (closing lines)

### Playoffs (4 weeks)
Run **48 hours before games**:
1. Update lines (check multiple sources)
2. Update weather forecasts
3. Run script
4. Review strong bets
5. Place bets day-of if weather stable

## Performance Tracking

The system exports a CSV each week:
```
betting_card_20260115.csv
```

Track these metrics over time:
- Win rate on STRONG BET recommendations (target: 55%+)
- Average edge on winning bets vs losing bets
- ROI by signal type
- Accuracy vs closing line value (CLV)

## Tips for Success

### ✅ DO
- **Bet selectively** - only STRONG BETs with 3+ point edge
- **Verify lines** before placing bets (they move!)
- **Track results** to validate model performance
- **Update weather** close to game time
- **Shop lines** across multiple sportsbooks

### ❌ DON'T
- **Bet every game** - quality over quantity
- **Ignore warnings** - they exist for a reason
- **Chase losses** - stick to Kelly sizing
- **Bet LEAN signals** unless you're confident
- **Bet stale lines** - always use current market

## Example Weekly Session

```bash
$ python weekly_betting_card.py

Loading 2025 season data...
Initializing predictor...
Running predictions...

Analyzing HOU @ KC...
Analyzing WAS @ DET...
Analyzing LA @ PHI...
Analyzing BAL @ BUF...

================================================================================
🏈 WEEKLY BETTING CARD 🏈
================================================================================
Generated: 2026-01-15 05:30 PM
Bankroll: $10,000
================================================================================

STRONG BET (1 games)
================================================================================
🎯 STRONG BET: BAL +1.5
[... full details ...]

MEDIUM BET (1 games)
================================================================================
📊 MEDIUM BET: LA +6
[... full details ...]

LEAN (1 games)
================================================================================
👀 LEAN: HOU +8.5
[... full details ...]

NO PLAY (1 games)
================================================================================
❌ NO PLAY: WAS +9
[... full details ...]

📊 SUMMARY
================================================================================
Strong Bets: 1
Total Suggested Units: 2.5
Total Risk: $250 (2.5% of bankroll)
================================================================================

🔥 QUICK REFERENCE: STRONG BETS ONLY
================================================================================

BAL @ BUF
  → BET: BAL +1.5
  → UNITS: 2.5 ($250)
  → EDGE: 2.0 points

Good luck! 🍀
```

## Advanced: Line Shopping

If you have accounts at multiple sportsbooks:
1. Check all books for best line
2. Update market_lines with best available
3. A half-point difference can add significant value

Example:
- DraftKings: BAL +1.5
- FanDuel: BAL +2
- **Bet FanDuel** (0.5 point better = ~2% win probability increase)

## Questions?

- Model says +3 but market is +6: **AVOID** (model likely wrong)
- Model says -7 but market is -3: **STRONG BET HOME TEAM** (4pt edge)
- No strong bets this week: **WAIT** (patience = profitability)

Remember: **You don't need to bet every week. Wait for spots where your model has a clear edge.**
