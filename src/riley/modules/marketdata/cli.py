"""Command-line interface for market data collection"""
import argparse
import sys
from pathlib import Path
import logging

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from riley.modules.marketdata.yfinance_collector import (
    backfill_symbols,
    fetch_daily_update,
    RRG_SECTOR_UNIVERSE
)
from riley.modules.marketdata.store import store_price_bars, get_latest_date, get_bar_count
from riley.modules.marketdata.export_rrg import export_rrg_sectors, get_export_stats

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cmd_backfill(args):
    """Backfill historical price data"""
    symbols = args.symbols if args.symbols else RRG_SECTOR_UNIVERSE

    logger.info(f"Starting backfill for {len(symbols)} symbols")
    logger.info(f"Lookback: {args.lookback_days} days")

    # Collect data
    results = backfill_symbols(
        symbols=symbols,
        lookback_days=args.lookback_days,
        end_date=args.end_date
    )

    # Store in database
    total_bars = 0
    for symbol, df in results.items():
        rows = store_price_bars(df)
        total_bars += rows
        logger.info(f"  {symbol}: {rows} bars")

    logger.info(f"\n✅ Backfill complete: {total_bars} total bars stored")

    # Show stats
    if args.export:
        export_path = args.export
        export_rrg_sectors(export_path, lookback_days=args.lookback_days)


def cmd_update(args):
    """Update with latest price data"""
    symbols = args.symbols if args.symbols else RRG_SECTOR_UNIVERSE

    logger.info(f"Starting daily update for {len(symbols)} symbols")
    logger.info(f"Overlap window: {args.overlap_days} days")

    # Collect recent data
    results = fetch_daily_update(
        symbols=symbols,
        lookback_days=args.overlap_days
    )

    # Store in database
    total_bars = 0
    for symbol, df in results.items():
        rows = store_price_bars(df)
        total_bars += rows
        logger.info(f"  {symbol}: {rows} bars")

    logger.info(f"\n✅ Update complete: {total_bars} total bars upserted")

    # Export if requested
    if args.export:
        export_path = args.export
        export_rrg_sectors(export_path, lookback_days=365)


def cmd_export(args):
    """Export data to RRG CSV format"""
    logger.info(f"Exporting RRG data to {args.output}")

    export_rrg_sectors(
        output_path=args.output,
        lookback_days=args.lookback_days
    )

    logger.info("✅ Export complete")


def cmd_stats(args):
    """Show database statistics"""
    stats = get_export_stats()

    print("\n" + "="*60)
    print("RILEY MARKET DATA STATISTICS")
    print("="*60)
    print(f"\nTotal Symbols: {stats['total_symbols']}")
    print(f"Total Bars: {stats['total_bars']:,}")
    print(f"Date Range: {stats['date_range']['min']} to {stats['date_range']['max']}")

    print(f"\nPer-Symbol Breakdown:")
    print("-" * 60)
    print(f"{'Symbol':<8} {'Bars':>8} {'Start Date':<12} {'End Date':<12}")
    print("-" * 60)

    for sym_info in stats['symbols']:
        print(f"{sym_info['symbol']:<8} {sym_info['bars']:>8,} "
              f"{sym_info['min_date']:<12} {sym_info['max_date']:<12}")

    print("="*60 + "\n")


def cmd_verify(args):
    """Verify data completeness for RRG universe"""
    logger.info("Verifying RRG sector universe data...")

    print("\n" + "="*60)
    print("RRG SECTOR UNIVERSE VERIFICATION")
    print("="*60)

    all_good = True
    for symbol in RRG_SECTOR_UNIVERSE:
        bar_count = get_bar_count(symbol)
        latest = get_latest_date(symbol)

        status = "✅" if bar_count > 0 else "❌"
        print(f"{status} {symbol:<6} {bar_count:>5} bars  Latest: {latest or 'NO DATA'}")

        if bar_count == 0:
            all_good = False

    print("="*60)

    if all_good:
        print("\n✅ All RRG symbols have data\n")
    else:
        print("\n⚠️  Some symbols missing data - run backfill\n")

    return 0 if all_good else 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Riley Market Data Collector',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backfill 2 years of data for RRG sectors
  python cli.py backfill --lookback-days 730

  # Daily update with export
  python cli.py update --export artifacts/rrg/rrg_prices_daily.csv

  # Export specific date range
  python cli.py export --output data.csv --lookback-days 365

  # Show statistics
  python cli.py stats

  # Verify RRG universe data
  python cli.py verify
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Backfill command
    parser_backfill = subparsers.add_parser('backfill', help='Backfill historical data')
    parser_backfill.add_argument('--symbols', nargs='+', help='Symbols to backfill (default: RRG universe)')
    parser_backfill.add_argument('--lookback-days', type=int, default=730, help='Days to look back (default: 730)')
    parser_backfill.add_argument('--end-date', help='End date (YYYY-MM-DD, default: today)')
    parser_backfill.add_argument('--export', help='Export to CSV after backfill')
    parser_backfill.set_defaults(func=cmd_backfill)

    # Update command
    parser_update = subparsers.add_parser('update', help='Daily update (append latest bars)')
    parser_update.add_argument('--symbols', nargs='+', help='Symbols to update (default: RRG universe)')
    parser_update.add_argument('--overlap-days', type=int, default=10, help='Overlap window (default: 10)')
    parser_update.add_argument('--export', help='Export to CSV after update')
    parser_update.set_defaults(func=cmd_update)

    # Export command
    parser_export = subparsers.add_parser('export', help='Export to RRG CSV format')
    parser_export.add_argument('--output', required=True, help='Output CSV path')
    parser_export.add_argument('--lookback-days', type=int, default=365, help='Days to include (default: 365)')
    parser_export.set_defaults(func=cmd_export)

    # Stats command
    parser_stats = subparsers.add_parser('stats', help='Show database statistics')
    parser_stats.set_defaults(func=cmd_stats)

    # Verify command
    parser_verify = subparsers.add_parser('verify', help='Verify RRG universe data completeness')
    parser_verify.set_defaults(func=cmd_verify)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
