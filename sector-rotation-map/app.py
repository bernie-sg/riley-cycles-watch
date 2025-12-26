"""
Streamlit app for RRG Sector Rotation Map
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import io

from rrg import (
    load_csv, detect_mode, filter_by_date, get_sector_universe,
    prepare_table_data, compute_rrg_metrics, create_rrg_chart,
    US_SECTORS, DEFAULT_PARAMS
)

# Page config
st.set_page_config(
    page_title="Sector Rotation Map (RRG)",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Sector Rotation Map (RRG)")
st.markdown("Relative Rotation Graph for sector analysis")

# Sidebar controls
st.sidebar.header("⚙️ Controls")

# File upload
uploaded_file = st.sidebar.file_uploader(
    "Upload CSV Data",
    type=['csv'],
    help="Upload OHLCV data (Mode A) or precomputed metrics (Mode B)"
)

if uploaded_file is not None:
    # Load and process data
    try:
        # Save uploaded file temporarily
        df_raw, mode = load_csv(uploaded_file)

        st.sidebar.success(f"✓ Loaded {len(df_raw)} rows ({mode.upper()})")

        # Get date range
        min_date = df_raw['date'].min()
        max_date = df_raw['date'].max()

        # Benchmark selection
        available_symbols = sorted(df_raw['symbol'].unique())
        default_benchmark = 'SPY' if 'SPY' in available_symbols else available_symbols[0]

        benchmark_symbol = st.sidebar.selectbox(
            "Benchmark Symbol",
            available_symbols,
            index=available_symbols.index(default_benchmark) if default_benchmark in available_symbols else 0
        )

        # Mode A parameters (if needed)
        if mode == 'mode_a':
            with st.sidebar.expander("🔧 RRG Calculation Parameters"):
                rs_smoothing = st.slider(
                    "RS Smoothing Period",
                    min_value=5,
                    max_value=30,
                    value=DEFAULT_PARAMS['rs_smoothing'],
                    help="EMA period for smoothing relative strength"
                )
                ratio_lookback = st.slider(
                    "RS-Ratio Lookback",
                    min_value=5,
                    max_value=30,
                    value=DEFAULT_PARAMS['ratio_lookback'],
                    help="Rolling mean period for RS-Ratio calculation"
                )
                momentum_lookback = st.slider(
                    "RS-Momentum Lookback",
                    min_value=5,
                    max_value=30,
                    value=DEFAULT_PARAMS['momentum_lookback'],
                    help="Rolling mean period for RS-Momentum calculation"
                )

            # Compute RRG metrics
            with st.spinner("Computing RRG metrics..."):
                df_processed = compute_rrg_metrics(
                    df_raw,
                    benchmark_symbol=benchmark_symbol,
                    rs_smoothing=rs_smoothing,
                    ratio_lookback=ratio_lookback,
                    momentum_lookback=momentum_lookback
                )
        else:
            # Mode B: Use precomputed metrics
            df_processed = df_raw

        # Tail length
        tail_weeks = st.sidebar.slider(
            "Tail Length (weeks)",
            min_value=1,
            max_value=20,
            value=DEFAULT_PARAMS['tail_weeks'],
            help="Number of weeks to show in historical tail"
        )

        # End date selection
        end_date = st.sidebar.date_input(
            "End Date",
            value=max_date.date(),
            min_value=min_date.date(),
            max_value=max_date.date()
        )
        end_date = pd.Timestamp(end_date)

        # Visibility toggles
        col1, col2 = st.sidebar.columns(2)
        with col1:
            show_tails = st.checkbox("Show Tails", value=True)
        with col2:
            show_labels = st.checkbox("Show Labels", value=True)

        # Universe selection
        universe = st.sidebar.selectbox(
            "Sector Universe",
            ["US_SECTORS", "All Symbols"],
            index=0,
            help="Filter to specific sector universe"
        )

        # Get symbols to plot
        if universe == "US_SECTORS":
            symbols = get_sector_universe(df_processed, 'US_SECTORS')
            symbols = [s for s in symbols if s != benchmark_symbol]
        else:
            symbols = [s for s in df_processed['symbol'].unique() if s != benchmark_symbol]

        # Filter data to date range
        df_filtered = filter_by_date(df_processed, end_date.strftime('%Y-%m-%d'), tail_weeks)

        # Get benchmark price for title
        benchmark_price = None
        if mode == 'mode_a':
            benchmark_data = df_filtered[
                (df_filtered['symbol'] == benchmark_symbol) &
                (df_filtered['date'] == end_date)
            ]
            if not benchmark_data.empty and 'close' in benchmark_data.columns:
                benchmark_price = benchmark_data['close'].iloc[0]

        # Create chart
        st.subheader("Sector Rotation Map")
        fig = create_rrg_chart(
            df_filtered,
            symbols=symbols,
            end_date=end_date,
            tail_weeks=tail_weeks,
            show_tails=show_tails,
            show_labels=show_labels,
            benchmark_symbol=benchmark_symbol,
            benchmark_price=benchmark_price
        )

        # Display chart
        st.plotly_chart(fig, use_container_width=True)

        # Export button
        if st.sidebar.button("💾 Export Chart as PNG"):
            # Convert figure to image
            img_bytes = fig.to_image(format="png", width=1200, height=700)
            st.sidebar.download_button(
                label="Download PNG",
                data=img_bytes,
                file_name=f"sector_rotation_{end_date.strftime('%Y%m%d')}.png",
                mime="image/png"
            )

        # Table below chart
        st.subheader("Sector Details")

        table_df = prepare_table_data(df_filtered, mode, symbols, end_date)

        # Display table
        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True
        )

        # Export table data
        csv = table_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Table as CSV",
            data=csv,
            file_name=f"sector_details_{end_date.strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

        # Show data info
        with st.expander("ℹ️ Data Info"):
            st.write(f"**Mode:** {mode.upper()}")
            st.write(f"**Date Range:** {min_date.date()} to {max_date.date()}")
            st.write(f"**Symbols:** {len(symbols)}")
            st.write(f"**Benchmark:** {benchmark_symbol}")
            if mode == 'mode_a':
                st.write(f"**RS Smoothing:** {rs_smoothing}")
                st.write(f"**Ratio Lookback:** {ratio_lookback}")
                st.write(f"**Momentum Lookback:** {momentum_lookback}")

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

else:
    # No file uploaded - show instructions
    st.info("👈 Upload a CSV file to begin")

    st.markdown("""
    ### How to Use

    1. **Upload CSV Data** (Mode A or Mode B)
    2. **Adjust parameters** in the sidebar
    3. **View the rotation map** and sector table
    4. **Export** chart as PNG or table as CSV

    ### Data Formats

    #### Mode A: OHLCV Data (Computed RRG)
    Required columns:
    - `date` (YYYY-MM-DD)
    - `symbol` (e.g., XLK, SPY)
    - `close` (closing price)

    The app will compute RS-Ratio and RS-Momentum using configurable parameters.

    #### Mode B: Precomputed Metrics
    Required columns:
    - `date` (YYYY-MM-DD)
    - `symbol` (e.g., XLK, SPY)
    - `rs_ratio` (precomputed RS-Ratio)
    - `rs_momentum` (precomputed RS-Momentum)

    ### US Sector ETFs
    """)

    # Show sector list
    sector_df = pd.DataFrame([
        {'Symbol': sym, 'Name': name}
        for sym, name in US_SECTORS.items()
    ])
    st.table(sector_df)

    st.markdown("""
    ### Example CSV Templates

    Download example templates from the repository:
    - `examples/mode_a_template.csv` - OHLCV format
    - `examples/mode_b_template.csv` - Precomputed metrics format
    """)
