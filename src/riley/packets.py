"""Packet generation for Riley Project"""
import json
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd


def write_packets(symbol: str, as_of_date: str, df: pd.DataFrame,
                  pivots: List[Dict[str, Any]], vol_profile: Dict[str, Any],
                  range_context: Dict[str, Any], volatility_regime: Dict[str, Any],
                  trend_regime: Dict[str, Any], output_dir: Path,
                  cycle_pack: Dict[str, Any] = None,
                  data_quality: Dict[str, Any] = None) -> Path:
    """
    Write all packet files for an instrument run.

    Returns path to packet.json
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # context.json
    context = {
        'timebase': 'TRADING_BARS',
        'as_of_date': as_of_date,
        'symbol': symbol,
        'timeframe_coverage': {
            'start': df['timestamp'].min().isoformat(),
            'end': df['timestamp'].max().isoformat(),
            'total_bars': len(df),
            'td_index_range': f"0-{len(df)-1}" if len(df) > 0 else "0-0"
        },
        'volatility_regime': volatility_regime,
        'trend_regime': trend_regime,
        'notes': ''
    }

    # Add data quality reporting if provided
    if data_quality:
        context['data_quality'] = {
            'bars_dropped': data_quality.get('bars_dropped', 0),
            'drop_pct': round(data_quality.get('drop_pct', 0.0), 4),
            'reasons': data_quality.get('reasons', {})
        }

    _write_json(output_dir / 'context.json', context)

    # levels.json
    levels_list = []

    # Add pivots as tier 1
    for i, pivot in enumerate(pivots[:5]):  # Top 5 pivots
        levels_list.append({
            'tier': 1,
            'level_price': pivot['price'],
            'source': 'pivot',
            'label': f"SWING_{pivot['type']}",
            'date': pivot['date'].isoformat()
        })

    # Add POCs as tier 2
    if vol_profile.get('poc_252td'):
        levels_list.append({
            'tier': 2,
            'level_price': vol_profile['poc_252td'],
            'source': 'volume_profile',
            'label': '252TD_POC',
            'window': '252 trading days',
            'date': None
        })

    if vol_profile.get('poc_180td'):
        levels_list.append({
            'tier': 2,
            'level_price': vol_profile['poc_180td'],
            'source': 'volume_profile',
            'label': '180TD_POC',
            'window': '180 trading days',
            'date': None
        })

    if vol_profile.get('poc_90td'):
        levels_list.append({
            'tier': 2,
            'level_price': vol_profile['poc_90td'],
            'source': 'volume_profile',
            'label': '90TD_POC',
            'window': '90 trading days',
            'date': None
        })

    # Add range levels as tier 3
    for window_key, window_label in [('20td', '20 trading days'), ('60td', '60 trading days'), ('252td', '252 trading days')]:
        if window_key in range_context:
            r = range_context[window_key]
            levels_list.append({
                'tier': 3,
                'level_price': r['high'],
                'source': 'range',
                'label': f'{window_key.upper()}_HIGH',
                'window': window_label,
                'date': None
            })
            levels_list.append({
                'tier': 3,
                'level_price': r['low'],
                'source': 'range',
                'label': f'{window_key.upper()}_LOW',
                'window': window_label,
                'date': None
            })

    levels = {'levels': levels_list}
    _write_json(output_dir / 'levels.json', levels)

    # pivots.json
    pivots_serializable = []
    for p in pivots:
        pivots_serializable.append({
            'type': p['type'],
            'price': p['price'],
            'date': p['date'].isoformat(),
            'index': p['index']
        })
    _write_json(output_dir / 'pivots.json', {'pivots': pivots_serializable})

    # volume.json
    _write_json(output_dir / 'volume.json', vol_profile)

    # gamma.json (placeholder)
    gamma = {
        'status': 'missing',
        'reason': 'Gamma data not available in Phase 1'
    }
    _write_json(output_dir / 'gamma.json', gamma)

    # diff.json (placeholder for first run)
    diff = {
        'status': 'no_previous_run',
        'price_change': None,
        'new_pivots': [],
        'level_changes': []
    }
    _write_json(output_dir / 'diff.json', diff)

    # packet.json (master file)
    packet = {
        'symbol': symbol,
        'as_of_date': as_of_date,
        'generated_at': pd.Timestamp.now().isoformat(),
        'files': {
            'context': str(output_dir / 'context.json'),
            'levels': str(output_dir / 'levels.json'),
            'pivots': str(output_dir / 'pivots.json'),
            'volume': str(output_dir / 'volume.json'),
            'gamma': str(output_dir / 'gamma.json'),
            'diff': str(output_dir / 'diff.json')
        },
        'cycles': cycle_pack if cycle_pack else {'status': 'missing'}
    }
    packet_path = output_dir / 'packet.json'
    _write_json(packet_path, packet)

    return packet_path


def _write_json(path: Path, data: Dict[str, Any]):
    """Write JSON with pretty formatting"""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Packet written: {path}")
