"""Test astro events functionality"""
import sys
from pathlib import Path
import tempfile
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from riley.database import Database
from riley.views import generate_watchlist_snapshot, generate_window_countdown


def test_add_astro_event_primary():
    """Test adding PRIMARY astro event"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db = Database(tmp.name)
        db.run_migrations()

        # Create instrument and calendar
        db.upsert_instrument(symbol='ES', role='CANONICAL', canonical_symbol='ES', name='E-mini S&P 500')
        db.upsert_daily_calendar('ES', [
            {'td_index': i, 'trading_date_label': f'2025-01-{i+1:02d}'}
            for i in range(31)
        ])

        # Add PRIMARY astro event
        astro_id = db.add_astro_event(
            instrument_symbol='ES',
            event_label='2025-01-15',
            role='PRIMARY',
            name='Mars Square',
            category='REVERSAL',
            confidence=80,
            source='Ephemeris',
            notes='Major aspect'
        )

        assert astro_id is not None

        # Verify td_index was resolved correctly (2025-01-15 should map to td_index=14)
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT td_index, event_label FROM astro_events WHERE astro_id = ?", (astro_id,))
        row = cursor.fetchone()
        assert row['td_index'] == 14
        assert row['event_label'] == '2025-01-15'

        db.close()
        Path(tmp.name).unlink()

    print("✓ Add PRIMARY astro event works correctly")


def test_add_astro_event_backup():
    """Test adding BACKUP astro event"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db = Database(tmp.name)
        db.run_migrations()

        # Create instrument and calendar
        db.upsert_instrument(symbol='ES', role='CANONICAL', canonical_symbol='ES', name='E-mini S&P 500')
        db.upsert_daily_calendar('ES', [
            {'td_index': i, 'trading_date_label': f'2025-01-{i+1:02d}'}
            for i in range(31)
        ])

        # Add BACKUP astro event
        astro_id = db.add_astro_event(
            instrument_symbol='ES',
            event_label='2025-01-20',
            role='BACKUP',
            name='Venus Trine',
            category='LIQUIDITY',
            confidence=60
        )

        assert astro_id is not None

        db.close()
        Path(tmp.name).unlink()

    print("✓ Add BACKUP astro event works correctly")


def test_list_upcoming_astro():
    """Test list_upcoming_astro returns correct ordering"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db = Database(tmp.name)
        db.run_migrations()

        # Create instrument and calendar
        db.upsert_instrument(symbol='ES', role='CANONICAL', canonical_symbol='ES', name='E-mini S&P 500')
        db.upsert_daily_calendar('ES', [
            {'td_index': i, 'trading_date_label': f'2025-01-{i+1:02d}'}
            for i in range(31)
        ])

        # Add PRIMARY events
        db.add_astro_event('ES', '2025-01-15', 'PRIMARY', name='Mars Square', category='REVERSAL')
        db.add_astro_event('ES', '2025-01-25', 'PRIMARY', name='Jupiter Trine', category='REVERSAL')

        # Add BACKUP events
        db.add_astro_event('ES', '2025-01-08', 'BACKUP', name='Venus Conjunction')
        db.add_astro_event('ES', '2025-01-12', 'BACKUP', name='Mercury Aspect')
        db.add_astro_event('ES', '2025-01-18', 'BACKUP', name='Moon Node')

        # Query from asof td_index=5 (2025-01-06), horizon=15
        astro_data = db.list_upcoming_astro('ES', asof_td_index=5, horizon_td=15)

        # Should get next PRIMARY after td_index=5 (Mars Square at td_index=14)
        assert astro_data['next_primary'] is not None
        assert astro_data['next_primary']['event_label'] == '2025-01-15'
        assert astro_data['next_primary']['name'] == 'Mars Square'

        # Should get BACKUP events within horizon (td_index 5-19)
        # Venus Conjunction (td_index=7), Mercury Aspect (td_index=11), Moon Node (td_index=17)
        assert len(astro_data['backup_events']) == 3
        assert astro_data['backup_events'][0]['event_label'] == '2025-01-08'
        assert astro_data['backup_events'][1]['event_label'] == '2025-01-12'
        assert astro_data['backup_events'][2]['event_label'] == '2025-01-18'

        db.close()
        Path(tmp.name).unlink()

    print("✓ list_upcoming_astro returns correct ordering")


def test_watchlist_snapshot_includes_astro():
    """Test watchlist snapshot includes astro section"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db = Database(tmp.name)
        db.run_migrations()

        # Create instrument and calendar
        db.upsert_instrument(symbol='ES', role='CANONICAL', canonical_symbol='ES', name='E-mini S&P 500')
        db.upsert_daily_calendar('ES', [
            {'td_index': i, 'trading_date_label': f'2025-01-{i+1:02d}'}
            for i in range(31)
        ])

        # Create cycle spec and projection
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = 'ES'")
        instrument_id = cursor.fetchone()[0]

        cycle_id = db.create_cycle_spec(
            instrument_symbol='ES',
            timeframe='DAILY',
            anchor_input_date_label='2025-01-10',
            cycle_length_bars=10,
            window_minus_bars=2,
            window_plus_bars=2,
            prewindow_lead_bars=1,
            source='test'
        )

        db.write_cycle_projections(cycle_id, 1, [{
            'instrument_id': instrument_id,
            'timeframe': 'DAILY',
            'anchor_index': 9,
            'anchor_label': '2025-01-10',
            'k': 0,
            'median_index': 9,
            'median_label': '2025-01-10',
            'core_start_index': 7,
            'core_end_index': 11,
            'prewindow_start_index': 6,
            'prewindow_end_index': 6,
            'active': 1
        }])

        # Add astro events
        db.add_astro_event('ES', '2025-01-15', 'PRIMARY', name='Mars Square', category='REVERSAL', confidence=80)
        db.add_astro_event('ES', '2025-01-08', 'BACKUP', name='Venus Conjunction', category='LIQUIDITY')
        db.add_astro_event('ES', '2025-01-12', 'BACKUP', name='Mercury Aspect', category='VOL')

        # Generate snapshot
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot = generate_watchlist_snapshot(
                db=db,
                symbol='ES',
                asof_td_label='2025-01-05',
                notes_limit=3,
                out_root=Path(tmpdir)
            )

            # Verify astro section exists
            assert 'astro' in snapshot
            assert snapshot['astro']['next_primary'] is not None
            assert snapshot['astro']['next_primary']['date'] == '2025-01-15'
            assert snapshot['astro']['next_primary']['name'] == 'Mars Square'
            assert snapshot['astro']['next_primary']['t_minus_td'] == 10  # td_index 14 - 4 = 10

            assert len(snapshot['astro']['backup_events']) == 2  # Within horizon of 15
            assert snapshot['astro']['backup_events'][0]['date'] == '2025-01-08'
            assert snapshot['astro']['backup_events'][1]['date'] == '2025-01-12'

            # Verify markdown includes astro section
            snapshot_dir = Path(tmpdir) / "watchlist" / "ES" / "2025-01-05"
            assert (snapshot_dir / "snapshot.md").exists()

            with open(snapshot_dir / "snapshot.md") as f:
                md_content = f.read()
                assert "## Astro Events" in md_content
                assert "Mars Square" in md_content
                assert "Venus Conjunction" in md_content

        db.close()
        Path(tmp.name).unlink()

    print("✓ Watchlist snapshot includes astro section")


def test_countdown_includes_astro_columns():
    """Test countdown view includes astro columns"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db = Database(tmp.name)
        db.run_migrations()

        # Create two instruments
        db.upsert_instrument(symbol='ES', role='CANONICAL', canonical_symbol='ES', name='E-mini S&P 500')
        db.upsert_instrument(symbol='NQ', role='CANONICAL', canonical_symbol='NQ', name='E-mini NASDAQ')

        for symbol in ['ES', 'NQ']:
            db.upsert_daily_calendar(symbol, [
                {'td_index': i, 'trading_date_label': f'2025-01-{i+1:02d}'}
                for i in range(31)
            ])

        # Add astro events
        db.add_astro_event('ES', '2025-01-15', 'PRIMARY', name='Mars Square')
        db.add_astro_event('ES', '2025-01-08', 'BACKUP', name='Venus Conjunction')
        db.add_astro_event('NQ', '2025-01-20', 'PRIMARY', name='Jupiter Trine')

        # Generate countdown
        with tempfile.TemporaryDirectory() as tmpdir:
            countdown = generate_window_countdown(
                db=db,
                asof_td_label='2025-01-05',
                horizon_td=15,
                horizon_tw=6,
                out_root=Path(tmpdir)
            )

            # Verify astro columns exist
            assert len(countdown['rows']) >= 2
            for row in countdown['rows']:
                assert 'primary_astro' in row
                assert 'backup_astro' in row

            # Find ES row
            es_row = next((r for r in countdown['rows'] if r['symbol'] == 'ES'), None)
            assert es_row is not None
            assert es_row['primary_astro'] == '2025-01-15 (T-10)'
            assert es_row['backup_astro'] == '2025-01-08 (T-3)'

            # Find NQ row
            nq_row = next((r for r in countdown['rows'] if r['symbol'] == 'NQ'), None)
            assert nq_row is not None
            assert nq_row['primary_astro'] == '2025-01-20 (T-15)'

            # Verify markdown includes astro columns
            countdown_dir = Path(tmpdir) / "countdown" / "2025-01-05"
            assert (countdown_dir / "countdown.md").exists()

            with open(countdown_dir / "countdown.md") as f:
                md_content = f.read()
                assert "Primary Astro (TD)" in md_content
                assert "Backup Astro (TD)" in md_content

        db.close()
        Path(tmp.name).unlink()

    print("✓ Countdown view includes astro columns")


if __name__ == '__main__':
    test_add_astro_event_primary()
    test_add_astro_event_backup()
    test_list_upcoming_astro()
    test_watchlist_snapshot_includes_astro()
    test_countdown_includes_astro_columns()
    print("\n✓ All astro events tests passed")
