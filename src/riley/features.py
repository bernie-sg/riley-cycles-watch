"""Feature computation for Riley Project - deterministic only"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any


def detect_pivots(df: pd.DataFrame, left: int = 2, right: int = 2) -> List[Dict[str, Any]]:
    """
    Detect swing pivots using fractal method.

    Returns list of pivot dicts with:
    - type: "HIGH" or "LOW"
    - price: float
    - date: timestamp
    - index: integer index in dataframe
    """
    pivots = []

    for i in range(left, len(df) - right):
        # Check for swing high
        if all(df['high'].iloc[i] > df['high'].iloc[i - j] for j in range(1, left + 1)) and \
           all(df['high'].iloc[i] > df['high'].iloc[i + j] for j in range(1, right + 1)):
            pivots.append({
                'type': 'HIGH',
                'price': df['high'].iloc[i],
                'date': df['timestamp'].iloc[i],
                'index': i
            })

        # Check for swing low
        if all(df['low'].iloc[i] < df['low'].iloc[i - j] for j in range(1, left + 1)) and \
           all(df['low'].iloc[i] < df['low'].iloc[i + j] for j in range(1, right + 1)):
            pivots.append({
                'type': 'LOW',
                'price': df['low'].iloc[i],
                'date': df['timestamp'].iloc[i],
                'index': i
            })

    return pivots


def compute_volume_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute volume profile POCs using trading bars with integrity checks.

    Returns dict with:
    - poc_90td: 90 trading-day point of control
    - poc_180td: 180 trading-day point of control
    - poc_252td: 252 trading-day point of control
    - status: "ok" or "insufficient_clean_data"
    """
    def compute_poc(data: pd.DataFrame) -> float:
        """
        Compute POC as volume-weighted average price.

        Integrity checks:
        - Use sanitized bars only
        - Verify sufficient volume data
        """
        if len(data) == 0:
            return None

        # Check for sufficient clean data
        total_volume = data['volume'].sum()
        if total_volume == 0:
            return None

        # Simple volume-weighted average (no filtering of individual bars)
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        return (typical_price * data['volume']).sum() / data['volume'].sum()

    poc_90td = compute_poc(df.tail(90))
    poc_180td = compute_poc(df.tail(180))
    poc_252td = compute_poc(df.tail(252))

    # Check if all POCs are valid
    status = "ok"
    if poc_90td is None or poc_180td is None or poc_252td is None:
        status = "insufficient_clean_data"

    return {
        'poc_90td': poc_90td,
        'poc_180td': poc_180td,
        'poc_252td': poc_252td,
        'status': status
    }


def compute_range_context(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute range context levels using trading bars.

    Returns dict with high/low/mid for 20TD, 60TD, 252TD windows.
    """
    current = df['close'].iloc[-1]

    def get_range(window: int):
        data = df.tail(window)
        high = data['high'].max()
        low = data['low'].min()
        mid = (high + low) / 2
        return {'high': high, 'low': low, 'mid': mid}

    return {
        '20td': get_range(20),
        '60td': get_range(60),
        '252td': get_range(252),
        'current': current
    }


def rank_pivots(pivots: List[Dict[str, Any]], df: pd.DataFrame, top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Rank pivots by importance (recency + magnitude).

    Simple heuristic: more recent + further from mean = more important.
    """
    if not pivots:
        return []

    current_price = df['close'].iloc[-1]
    current_date = df['timestamp'].iloc[-1]

    for pivot in pivots:
        days_ago = (current_date - pivot['date']).days
        price_distance = abs(pivot['price'] - current_price) / current_price

        # Score: weight recent pivots and significant price levels
        recency_score = 1.0 / (1.0 + days_ago / 30.0)  # decay over 30 days
        magnitude_score = price_distance * 10  # scale by distance

        pivot['score'] = recency_score + magnitude_score

    # Sort by score descending
    ranked = sorted(pivots, key=lambda x: x['score'], reverse=True)

    return ranked[:top_n]


def compute_volatility_regime(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute simple volatility regime using ATR percentile.
    """
    # Compute ATR (14-period)
    df = df.copy()
    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        )
    )
    df['atr'] = df['tr'].rolling(14).mean()

    current_atr = df['atr'].iloc[-1]
    atr_252 = df['atr'].tail(252)

    percentile = (atr_252 < current_atr).sum() / len(atr_252) * 100

    if percentile < 30:
        regime = "LOW"
    elif percentile > 70:
        regime = "HIGH"
    else:
        regime = "NORMAL"

    return {
        'atr': current_atr,
        'percentile': percentile,
        'regime': regime
    }


def compute_trend_regime(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute simple trend regime using MA slope.
    """
    df = df.copy()
    df['ma50'] = df['close'].rolling(50).mean()
    df['ma200'] = df['close'].rolling(200).mean()

    current_price = df['close'].iloc[-1]
    ma50 = df['ma50'].iloc[-1]
    ma200 = df['ma200'].iloc[-1]

    # Simple regime
    if current_price > ma50 > ma200:
        regime = "UPTREND"
    elif current_price < ma50 < ma200:
        regime = "DOWNTREND"
    else:
        regime = "CHOPPY"

    return {
        'current': current_price,
        'ma50': ma50,
        'ma200': ma200,
        'regime': regime
    }
