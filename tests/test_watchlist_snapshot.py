"""Test watchlist snapshot generation"""
import sys
from pathlib import Path
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from riley.database import Database
from riley.views import generate_watchlist_snapshot


def test_watchlist_snapshot_basic():
    """Test basic watchlist snapshot generation"""
    # Use in-memory database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db = Database(tmp.name)
        db.run_migrations()

        # Create test instrument
        db.upsert_instrument(symbol='TEST', role='CANONICAL', canonical_symbol='TEST', name='Test Instrument')
        db.upsert_instrument(symbol='TESTALIAS', role='ALIAS', canonical_symbol='TEST', alias_of_symbol='TEST')

        # Create calendar
        db.upsert_daily_calendar('TEST', [
            {'td_index': i, 'trading_date_label': f'2025-01-{i+1:02d}'}
            for i in range(20)
        ])

        # Create cycle spec
        cycle_id = db.create_cycle_spec(
            instrument_symbol='TEST',
            timeframe='DAILY',
            anchor_input_date_label='2025-01-05',
            cycle_length_bars=10,
            window_minus_bars=2,
            window_plus_bars=2,
            prewindow_lead_bars=1,
            source='test'
        )

        # Get instrument_id
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = 'TEST'")
        instrument_id = cursor.fetchone()[0]

        # Create projection
        db.write_cycle_projections(cycle_id, 1, [{
            'instrument_id': instrument_id,
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

        # Create desk note
        import json
        db.create_desk_note(
            instrument_symbol='TEST',
            asof_td_label='2025-01-03',
            author='TestAuthor',
            timeframe_scope='DAILY',
            note_type='SUMMARY',
            price_reference='OTHER',
            bullets_json=json.dumps(['Test bullet 1', 'Test bullet 2'])
        )

        # Generate snapshot
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot = generate_watchlist_snapshot(
                db=db,
                symbol='TEST',
                asof_td_label='2025-01-03',
                notes_limit=3,
                out_root=Path(tmpdir)
            )

            # Verify snapshot structure
            assert snapshot['symbol'] == 'TEST'
            assert 'TESTALIAS' in snapshot['aliases']
            assert snapshot['asof_td_label'] == '2025-01-03'
            assert 'DAILY' in snapshot['cycle_specs']
            assert snapshot['cycle_specs']['DAILY']['version'] == 1
            assert 'DAILY' in snapshot['cycle_proximity']
            assert snapshot['cycle_proximity']['DAILY']['status'] == 'IN_WINDOW'
            assert len(snapshot['notes']) == 1

            # Verify files were created
            snapshot_dir = Path(tmpdir) / "watchlist" / "TEST" / "2025-01-03"
            assert (snapshot_dir / "snapshot.md").exists()
            assert (snapshot_dir / "snapshot.json").exists()

        db.close()
        Path(tmp.name).unlink()

    print("✓ Watchlist snapshot generation works correctly")


if __name__ == '__main__':
    test_watchlist_snapshot_basic()
    print("\n✓ All watchlist snapshot tests passed")
