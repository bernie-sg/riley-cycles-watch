"""Test window countdown view generation"""
import sys
from pathlib import Path
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from riley.database import Database
from riley.views import generate_window_countdown


def test_window_countdown_basic():
    """Test basic window countdown generation"""
    # Use in-memory database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db = Database(tmp.name)
        db.run_migrations()

        # Create multiple test instruments with different statuses
        db.upsert_instrument(symbol='TEST1', role='CANONICAL', canonical_symbol='TEST1', name='Test Instrument 1')
        db.upsert_instrument(symbol='TEST2', role='CANONICAL', canonical_symbol='TEST2', name='Test Instrument 2')
        db.upsert_instrument(symbol='TEST3', role='CANONICAL', canonical_symbol='TEST3', name='Test Instrument 3')

        # Create calendars for all instruments (20 days, 4 weeks)
        for symbol in ['TEST1', 'TEST2', 'TEST3']:
            db.upsert_daily_calendar(symbol, [
                {'td_index': i, 'trading_date_label': f'2025-01-{i+1:02d}'}
                for i in range(20)
            ])
            db.upsert_weekly_calendar(symbol, [
                {'tw_index': i, 'week_end_label': f'2025-01-{(i+1)*5:02d}'}
                for i in range(4)
            ])

        # Get instrument IDs
        conn = db.connect()
        cursor = conn.cursor()
        instrument_ids = {}
        for symbol in ['TEST1', 'TEST2', 'TEST3']:
            cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = ?", (symbol,))
            instrument_ids[symbol] = cursor.fetchone()[0]

        # TEST1: Daily IN_WINDOW (high priority)
        # Asof is 2025-01-03 (td_index=2), so we want a core window containing index 2
        cycle_id1 = db.create_cycle_spec(
            instrument_symbol='TEST1',
            timeframe='DAILY',
            anchor_input_date_label='2025-01-05',
            cycle_length_bars=10,
            window_minus_bars=2,
            window_plus_bars=2,
            prewindow_lead_bars=1,
            source='test'
        )
        db.write_cycle_projections(cycle_id1, 1, [{
            'instrument_id': instrument_ids['TEST1'],
            'timeframe': 'DAILY',
            'anchor_index': 4,
            'anchor_label': '2025-01-05',
            'k': 0,
            'median_index': 4,
            'median_label': '2025-01-05',
            'core_start_index': 2,
            'core_end_index': 6,
            'prewindow_start_index': 1,
            'prewindow_end_index': 1,
            'active': 1
        }])

        # TEST2: Daily PREWINDOW (medium priority)
        cycle_id2 = db.create_cycle_spec(
            instrument_symbol='TEST2',
            timeframe='DAILY',
            anchor_input_date_label='2025-01-03',
            cycle_length_bars=10,
            window_minus_bars=2,
            window_plus_bars=2,
            prewindow_lead_bars=3,
            source='test'
        )
        db.write_cycle_projections(cycle_id2, 1, [{
            'instrument_id': instrument_ids['TEST2'],
            'timeframe': 'DAILY',
            'anchor_index': 2,
            'anchor_label': '2025-01-03',
            'k': 1,
            'median_index': 12,
            'median_label': '2025-01-13',
            'core_start_index': 10,
            'core_end_index': 14,
            'prewindow_start_index': 7,
            'prewindow_end_index': 9,
            'active': 1
        }])

        # TEST3: Weekly IN_WINDOW
        # For weekly, asof 2025-01-03 maps to tw_index=0 (first week ending 2025-01-05)
        cycle_id3 = db.create_cycle_spec(
            instrument_symbol='TEST3',
            timeframe='WEEKLY',
            anchor_input_date_label='2025-01-10',
            cycle_length_bars=4,
            window_minus_bars=1,
            window_plus_bars=1,
            prewindow_lead_bars=1,
            source='test'
        )
        db.write_cycle_projections(cycle_id3, 1, [{
            'instrument_id': instrument_ids['TEST3'],
            'timeframe': 'WEEKLY',
            'anchor_index': 1,
            'anchor_label': '2025-01-10',
            'k': 0,
            'median_index': 1,
            'median_label': '2025-01-10',
            'core_start_index': 0,
            'core_end_index': 2,
            'prewindow_start_index': -1,
            'prewindow_end_index': -1,
            'active': 1
        }])

        # Generate countdown
        with tempfile.TemporaryDirectory() as tmpdir:
            countdown = generate_window_countdown(
                db=db,
                asof_td_label='2025-01-03',
                horizon_td=15,
                horizon_tw=6,
                out_root=Path(tmpdir)
            )

            # Verify countdown structure
            assert countdown['asof_td_label'] == '2025-01-03'
            assert countdown['horizon_td'] == 15
            assert countdown['horizon_tw'] == 6
            assert len(countdown['rows']) == 3

            # Verify sorting (highest priority first)
            # TEST1 should be first (IN_WINDOW daily)
            assert countdown['rows'][0]['symbol'] == 'TEST1'
            assert countdown['rows'][0]['daily_status'] == 'IN_WINDOW'

            # Verify countdown values are computed
            for row in countdown['rows']:
                assert 'symbol' in row
                assert 'daily_status' in row
                assert 'weekly_status' in row
                assert 'priority_score' in row

            # Verify files were created
            countdown_dir = Path(tmpdir) / "countdown" / "2025-01-03"
            assert (countdown_dir / "countdown.md").exists()
            assert (countdown_dir / "countdown.json").exists()

        db.close()
        Path(tmp.name).unlink()

    print("✓ Window countdown generation works correctly")


if __name__ == '__main__':
    test_window_countdown_basic()
    print("\n✓ All window countdown tests passed")
