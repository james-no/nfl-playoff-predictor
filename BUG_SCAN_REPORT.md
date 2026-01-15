# Code Health & Bug Scan Report
**Date:** January 15, 2026  
**Status:** 🟡 Minor Issues Found

---

## 🔴 CRITICAL ISSUES (Fix Immediately)

### None Found ✅

---

## 🟡 HIGH PRIORITY ISSUES (Fix Before Production Use)

### 1. **Edge Percentage Calculation Bug**
**File:** `core/betting_signals.py:100`
```python
edge_percent = edge_points / abs(market_spread) if market_spread != 0 else 0
```

**Problem:** Division by zero protection, BUT returns 0 when spread is 0 (pick'em game)

**Edge Case:** 
- Model: Pick'em (0.0)
- Market: Pick'em (0.0)  
- Edge should be 0, but calculation shows 0/0 → 0% (misleading)

**Fix:**
```python
edge_percent = edge_points / abs(market_spread) if abs(market_spread) > 0.01 else float('inf')
```

**Impact:** Low (pick'em games are rare in playoffs)

---

### 2. **Kicker Stats Column Name Assumptions**
**File:** `core/kicker_analytics.py:32-70`

**Problem:** Assumes nflverse has columns:
- `field_goal_attempt`
- `kick_distance`
- `field_goal_result`
- `qtr`
- `score_differential`

**Risk:** If nflverse changes column names or these don't exist in 2025 data, function will crash

**Test:**
```python
# Check if columns exist
required_cols = ['field_goal_attempt', 'kick_distance', 'field_goal_result']
missing = [col for col in required_cols if col not in pbp.columns]
if missing:
    logger.warning(f"Missing kicker columns: {missing}")
    return _default_kicker_stats()
```

**Impact:** Medium (would crash on first run if columns missing)

---

### 3. **Weather Dict Keys Not Validated**
**File:** `weekly_betting_card.py:79-83`

**Problem:** Hardcoded weather dict passed to predictor:
```python
weather={
    'temperature': 35,
    'wind_speed': 10,
    'precipitation': 0
}
```

**Risk:** User forgets to update, uses placeholder values for actual games

**Fix:** Add validation:
```python
# At top of weekly_betting_card.py
WEATHER_FORECASTS = {
    "BUF @ DEN": {'temperature': 28, 'wind_speed': 12, 'precipitation': 0},
    "SF @ SEA": {'temperature': 45, 'wind_speed': 8, 'precipitation': 1},
    # ...
}

# In loop:
weather = WEATHER_FORECASTS.get(f"{game['away']} @ {game['home']}", None)
if weather is None:
    logger.warning(f"No weather data for {game}")
```

**Impact:** High (betting with wrong weather = bad picks)

---

## 🟢 MEDIUM PRIORITY ISSUES (Good to Fix)

### 4. **Date Consistency in CSV Export**
**File:** `weekly_betting_card.py:123`

```python
'date': datetime.now().strftime('%Y-%m-%d'),
```

**Problem:** Uses current datetime, not game date

**Issue:** If you run predictions on Wednesday for Saturday game, CSV shows Wednesday date

**Fix:**
```python
'date': datetime.now().strftime('%Y-%m-%d'),
'game_date': game.get('date', 'TBD'),  # Add actual game date
```

**Impact:** Low (tracking issue, not prediction issue)

---

### 5. **Bankroll Not Used in weekly_betting_card.py**
**File:** `weekly_betting_card.py:142`

```python
BANKROLL = 10000  # $10,000
# ... but then uses hardcoded 10000 on line 99
signal_generator = BettingSignalGenerator(bankroll=10000)
```

**Fix:**
```python
signal_generator = BettingSignalGenerator(bankroll=BANKROLL)
```

**Impact:** Low (just inconsistent)

---

### 6. **No Validation for Missing Prediction Fields**
**File:** `core/betting_signals.py:95-96`

```python
model_spread = model_prediction['predicted_spread']
model_prob = model_prediction['win_probability']
```

**Risk:** If predictor returns incomplete dict, KeyError crash

**Fix:**
```python
model_spread = model_prediction.get('predicted_spread')
model_prob = model_prediction.get('win_probability')

if model_spread is None or model_prob is None:
    raise ValueError(f"Invalid prediction for {game}: missing required fields")
```

**Impact:** Low (predictor always returns complete dict, but defensive coding is good)

---

## 🔵 LOW PRIORITY ISSUES (Nice to Have)

### 7. **Hard-Coded 2025 Season**
**File:** `weekly_betting_card.py:64`

```python
data_loader = NFLDataLoader(season=2025)
```

**Issue:** Will need manual update for 2026 season

**Fix:** Auto-detect from current date:
```python
from config import SeasonConfig
season, phase = SeasonConfig.get_current_season()
data_loader = NFLDataLoader(season=season)
```

**Impact:** Low (just need to remember to update next year)

---

### 8. **Playoff Validator Requires Manual Updates**
**File:** `utils/playoff_validator.py:30`

```python
CURRENT_ROUND = 'divisional'
```

**Issue:** Must manually update each week

**Improvement:** Add date-based auto-detection:
```python
def auto_detect_round():
    now = datetime.now()
    # Wild Card: Jan 11-13
    # Divisional: Jan 18-19
    # Conference: Jan 26
    # Super Bowl: Feb 9
    if now < datetime(2026, 1, 14):
        return 'wild_card'
    elif now < datetime(2026, 1, 20):
        return 'divisional'
    elif now < datetime(2026, 1, 27):
        return 'conference'
    else:
        return 'super_bowl'
```

**Impact:** Low (convenience feature)

---

### 9. **Kelly Calculation Doesn't Account for Spread Uncertainty**
**File:** `core/betting_signals.py:218`

```python
kelly = (b * p - q) / b
```

**Issue:** Uses point estimate of win_probability, doesn't account for model uncertainty

**Improvement:** Reduce Kelly for LOW confidence:
```python
if model_confidence == "LOW":
    fractional_kelly *= 0.5  # Half size for low confidence
elif model_confidence == "MEDIUM":
    fractional_kelly *= 0.75  # 75% size for medium confidence
```

**Impact:** Low (already happens via signal thresholds, but this would be more explicit)

---

### 10. **No Logging of Predictions**
**Files:** Multiple

**Issue:** If model crashes mid-run, lose all predictions

**Improvement:** Log predictions to file as they're generated:
```python
import json
with open(f'predictions_{datetime.now():%Y%m%d}.json', 'w') as f:
    json.dump(predictions, f, indent=2)
```

**Impact:** Low (can just re-run, takes <2 min)

---

## ✅ THINGS THAT ARE CORRECT

1. ✅ Kelly sizing with fractional Kelly (0.25) is safe
2. ✅ Key number logic is correct
3. ✅ Playoff validation prevents wrong teams
4. ✅ EPA calculations are bounded and capped
5. ✅ Division by zero protected in most places
6. ✅ Weather adjustments are sensible
7. ✅ CSV export works correctly
8. ✅ Error handling in kicker analytics (returns defaults)
9. ✅ Type hints used throughout
10. ✅ Logging is comprehensive

---

## 🚀 RECOMMENDED FIXES (In Priority Order)

### Immediate (Before This Weekend):
1. ✅ Add weather dict validation (Issue #3)
2. ✅ Fix bankroll variable inconsistency (Issue #5)
3. ✅ Add column existence check for kicker stats (Issue #2)

### Before Next Week:
4. ✅ Fix edge_percent division (Issue #1)
5. ✅ Add prediction field validation (Issue #6)
6. ✅ Add game dates to CSV export (Issue #4)

### Future Improvements:
7. Auto-detect season year (Issue #7)
8. Auto-detect playoff round (Issue #8)
9. Kelly adjustment for confidence (Issue #9)
10. Prediction logging (Issue #10)

---

## 🛡️ DEFENSIVE CODING CHECKLIST

Your code already does most of these:
- [x] Try/except blocks in critical sections
- [x] Default returns when data missing
- [x] Input validation (playoff teams)
- [ ] Column existence checking (kicker stats)
- [x] Division by zero protection
- [x] Type hints
- [x] Logging
- [ ] Assertion checks for critical assumptions

---

## 📊 Overall Code Health: **B+ (Very Good)**

**Strengths:**
- Professional architecture
- Good error handling
- Comprehensive logging
- Validation layer

**Weaknesses:**
- A few edge cases not handled
- Some hardcoded values
- Manual updates required weekly

**Verdict:** Code is production-ready with minor fixes. The high-priority issues are easy fixes that should be done before betting real money this weekend.

---

## 🔧 Quick Fix PR

Would you like me to create a branch with these fixes applied?
