"""IBKR data fetching for Riley Project"""
from ib_insync import IB, ContFuture, Index, util
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import time
from riley.ibkr_config import get_ibkr_host, get_ibkr_port


# IBKR Connection Configuration
IBKR_CLIENT_ID = 11


def connect_ibkr(host: str = None, port: int = None) -> IB:
    """
    Connect to Interactive Brokers TWS/Gateway.

    Args:
        host: IBKR host address (defaults to 192.168.0.18)
        port: IBKR port (defaults to 7496)

    Returns:
        IB: Connected IB instance

    Raises:
        ConnectionError: If connection fails after one retry
    """
    ib = IB()

    # Use provided parameters or defaults from config
    conn_host = host if host is not None else get_ibkr_host()
    conn_port = port if port is not None else get_ibkr_port()

    try:
        ib.connect(conn_host, conn_port, clientId=IBKR_CLIENT_ID, timeout=10)
        print(f"✓ Connected to IBKR at {conn_host}:{conn_port}")
        return ib

    except Exception as e:
        print(f"✗ Connection failed, retrying once... ({e})")
        time.sleep(2)

        try:
            ib.connect(conn_host, conn_port, clientId=IBKR_CLIENT_ID, timeout=10)
            print(f"✓ Connected to IBKR at {conn_host}:{conn_port} on retry")
            return ib

        except Exception as retry_error:
            raise ConnectionError(
                f"Failed to connect to IBKR at {conn_host}:{conn_port} after retry: {retry_error}"
            )


def fetch_ibkr_historical_bars(
    symbol: str,
    timeframe: str,
    start_date: Optional[datetime],
    end_date: datetime,
    host: str = None,
    port: int = None
) -> pd.DataFrame:
    """
    Fetch historical bars from IBKR.

    Args:
        symbol: Instrument symbol (ES or SPX)
        timeframe: "D" for daily, "W" for weekly
        start_date: Start date (if None, fetch max history)
        end_date: End date
        host: IBKR host (defaults to 192.168.0.18)
        port: IBKR port (defaults to 7496)

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume

    Raises:
        ValueError: If symbol not supported or invalid timeframe
        RuntimeError: If IBKR returns no data
    """
    # Phase 2.1: Hardcoded contract definitions
    # TODO: Move to config when supporting multiple instruments

    if symbol == "ES":
        # E-mini S&P 500 Futures (CME)
        # Using continuous contract (front month)
        contract = ContFuture(symbol="ES", exchange="CME", currency="USD")
        print(f"Contract: ES Continuous Futures (CME)")

    elif symbol == "SPX":
        # S&P 500 Index
        contract = Index(symbol="SPX", exchange="CBOE", currency="USD")
        print(f"Contract: SPX Index (CBOE)")

    else:
        raise ValueError(f"Unsupported symbol: {symbol}. Only ES and SPX supported in Phase 2.1")

    # Validate timeframe
    if timeframe not in ["D", "W"]:
        raise ValueError(f"Invalid timeframe: {timeframe}. Must be 'D' or 'W'")

    # Determine bar size and duration
    if timeframe == "D":
        bar_size = "1 day"
        # Fetch 15 years if no start date specified
        if start_date is None:
            duration = "15 Y"
        else:
            days = (end_date - start_date).days
            duration = f"{max(days, 1)} D"

    else:  # Weekly
        # Phase 2.1: Fetch daily bars and aggregate to weekly
        # This is more reliable than fetching weekly bars directly
        bar_size = "1 day"
        if start_date is None:
            duration = "15 Y"
        else:
            days = (end_date - start_date).days
            duration = f"{max(days, 1)} D"

    # Connect to IBKR
    ib = connect_ibkr(host=host, port=port)

    try:
        # Request historical data
        # For continuous contracts, use empty string for endDateTime
        if isinstance(contract, ContFuture):
            end_dt = ''  # Current time for continuous contracts
            print(f"Fetching {duration} of {bar_size} bars for {symbol} (continuous contract)")
        else:
            end_dt = end_date
            print(f"Fetching {duration} of {bar_size} bars for {symbol} ending {end_date.date()}")

        bars = ib.reqHistoricalData(
            contract,
            endDateTime=end_dt,
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow="TRADES",
            useRTH=True,  # Regular trading hours
            formatDate=1,  # UTC timestamps
            keepUpToDate=False
        )

        if not bars:
            raise RuntimeError(f"IBKR returned no data for {symbol}")

        print(f"✓ Received {len(bars)} bars from IBKR")

        # Convert to DataFrame
        df = util.df(bars)

        # Rename columns to standard schema
        df = df.rename(columns={
            'date': 'timestamp',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        })

        # Select only required columns
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        # Convert timestamp to datetime if needed
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

        # Filter by start_date if specified
        if start_date is not None:
            df = df[df['timestamp'] >= start_date]

        # If weekly timeframe, aggregate daily bars to weekly
        if timeframe == "W":
            df = _aggregate_to_weekly(df)
            print(f"✓ Aggregated to {len(df)} weekly bars")

        return df

    finally:
        ib.disconnect()
        print("✓ Disconnected from IBKR")


def _aggregate_to_weekly(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily bars to weekly bars.

    Weekly bars:
    - Week ends on Friday
    - Open = Monday's open (or first day of week)
    - High = max(high) for week
    - Low = min(low) for week
    - Close = Friday's close (or last day of week)
    - Volume = sum(volume) for week
    """
    df = daily_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Set timestamp as index for resampling
    df.set_index('timestamp', inplace=True)

    # Resample to weekly (W-FRI = week ending Friday)
    weekly = pd.DataFrame()
    weekly['open'] = df['open'].resample('W-FRI').first()
    weekly['high'] = df['high'].resample('W-FRI').max()
    weekly['low'] = df['low'].resample('W-FRI').min()
    weekly['close'] = df['close'].resample('W-FRI').last()
    weekly['volume'] = df['volume'].resample('W-FRI').sum()

    # Reset index to make timestamp a column
    weekly.reset_index(inplace=True)

    # Drop any rows with NaN (incomplete weeks)
    weekly.dropna(inplace=True)

    return weekly
