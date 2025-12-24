"""
Cycle Validation - Tripwire Consistency Checks

Validates cycle integrity before scan/UI operations.
Fails loudly if projections drift from specs.
"""

import sqlite3
from typing import Optional, List, Dict, Any


class CycleValidationError(Exception):
    """Raised when cycle validation fails"""
    pass


def validate_cycles(conn: sqlite3.Connection, symbol: Optional[str] = None) -> None:
    """
    Validate cycle consistency.
    Raises CycleValidationError on any violation.

    Args:
        conn: Database connection
        symbol: Optional symbol to validate (validates all if None)

    Raises:
        CycleValidationError: If any validation check fails
    """
    cursor = conn.cursor()
    errors = []

    # Filter condition
    symbol_filter = ""
    params = []
    if symbol:
        symbol_filter = " AND i.symbol = ?"
        params = [symbol]

    # Check 1: No duplicate projections
    query = f"""
        SELECT cp.instrument_id, cp.timeframe, cp.version, cp.k, COUNT(*) as count
        FROM cycle_projections cp
        JOIN instruments i ON i.instrument_id = cp.instrument_id
        WHERE i.role = 'CANONICAL'{symbol_filter}
        GROUP BY cp.instrument_id, cp.timeframe, cp.version, cp.k
        HAVING count > 1
    """
    cursor.execute(query, params)
    duplicates = cursor.fetchall()
    if duplicates:
        for dup in duplicates:
            errors.append(
                f"Duplicate projection: instrument_id={dup[0]}, "
                f"timeframe={dup[1]}, version={dup[2]}, k={dup[3]}, count={dup[4]}"
            )

    # Check 2: Exactly one k=0 active projection per active spec
    query = f"""
        SELECT i.symbol, cs.timeframe, cs.version, COUNT(cp.projection_id) as proj_count
        FROM cycle_specs cs
        JOIN instruments i ON i.instrument_id = cs.instrument_id
        LEFT JOIN cycle_projections cp
            ON cp.instrument_id = cs.instrument_id
            AND cp.timeframe = cs.timeframe
            AND cp.version = cs.version
            AND cp.k = 0
            AND cp.active = 1
        WHERE cs.status = 'ACTIVE'
            AND i.role = 'CANONICAL'{symbol_filter}
        GROUP BY i.symbol, cs.timeframe, cs.version
        HAVING proj_count != 1
    """
    cursor.execute(query, params)
    missing_or_extra = cursor.fetchall()
    if missing_or_extra:
        for row in missing_or_extra:
            errors.append(
                f"Expected exactly 1 projection for {row[0]} {row[1]} v{row[2]}, "
                f"found {row[3]}"
            )

    # Check 3: Math validation - DAILY
    query = f"""
        SELECT
            i.symbol,
            cs.timeframe,
            cs.version,
            cs.window_minus_bars,
            cs.window_plus_bars,
            cp.median_td_index,
            cp.core_start_td_index,
            cp.core_end_td_index
        FROM cycle_specs cs
        JOIN instruments i ON i.instrument_id = cs.instrument_id
        JOIN cycle_projections cp
            ON cp.instrument_id = cs.instrument_id
            AND cp.timeframe = cs.timeframe
            AND cp.version = cs.version
            AND cp.k = 0
        WHERE cs.status = 'ACTIVE'
            AND cs.timeframe = 'DAILY'
            AND i.role = 'CANONICAL'{symbol_filter}
    """
    cursor.execute(query, params)
    for row in cursor.fetchall():
        symbol, tf, version, minus, plus, median, start, end = row
        if start is None or median is None or end is None:
            errors.append(
                f"{symbol} DAILY v{version}: NULL indices (start={start}, median={median}, end={end})"
            )
            continue

        expected_start = median - minus
        expected_end = median + plus

        # Allow clamping to 0 for early dates
        if expected_start < 0:
            expected_start = 0

        if start != expected_start:
            errors.append(
                f"{symbol} DAILY v{version}: core_start_td_index mismatch. "
                f"Expected {expected_start} (median {median} - {minus}), got {start}"
            )
        if end != expected_end:
            errors.append(
                f"{symbol} DAILY v{version}: core_end_td_index mismatch. "
                f"Expected {expected_end} (median {median} + {plus}), got {end}"
            )

    # Check 4: Math validation - WEEKLY
    query = f"""
        SELECT
            i.symbol,
            cs.timeframe,
            cs.version,
            cs.window_minus_bars,
            cs.window_plus_bars,
            cp.median_tw_index,
            cp.core_start_tw_index,
            cp.core_end_tw_index
        FROM cycle_specs cs
        JOIN instruments i ON i.instrument_id = cs.instrument_id
        JOIN cycle_projections cp
            ON cp.instrument_id = cs.instrument_id
            AND cp.timeframe = cs.timeframe
            AND cp.version = cs.version
            AND cp.k = 0
        WHERE cs.status = 'ACTIVE'
            AND cs.timeframe = 'WEEKLY'
            AND i.role = 'CANONICAL'{symbol_filter}
    """
    cursor.execute(query, params)
    for row in cursor.fetchall():
        symbol, tf, version, minus, plus, median, start, end = row
        if start is None or median is None or end is None:
            errors.append(
                f"{symbol} WEEKLY v{version}: NULL indices (start={start}, median={median}, end={end})"
            )
            continue

        expected_start = median - minus
        expected_end = median + plus

        # Allow clamping to 0 for early dates
        if expected_start < 0:
            expected_start = 0

        if start != expected_start:
            errors.append(
                f"{symbol} WEEKLY v{version}: core_start_tw_index mismatch. "
                f"Expected {expected_start} (median {median} - {minus}), got {start}"
            )
        if end != expected_end:
            errors.append(
                f"{symbol} WEEKLY v{version}: core_end_tw_index mismatch. "
                f"Expected {expected_end} (median {median} + {plus}), got {end}"
            )

    # Check 5: Label resolution non-null
    query = f"""
        SELECT i.symbol, cp.timeframe, cp.version
        FROM cycle_projections cp
        JOIN instruments i ON i.instrument_id = cp.instrument_id
        WHERE cp.k = 0
            AND cp.active = 1
            AND i.role = 'CANONICAL'
            AND (cp.core_start_label IS NULL
                 OR cp.core_end_label IS NULL
                 OR cp.median_label IS NULL){symbol_filter}
    """
    cursor.execute(query, params)
    null_labels = cursor.fetchall()
    if null_labels:
        for row in null_labels:
            errors.append(
                f"{row[0]} {row[1]} v{row[2]}: NULL label columns"
            )

    # Check 6: No cross-calendar contamination
    query = f"""
        SELECT i.symbol, cp.timeframe, cp.version,
               cp.median_td_index, cp.median_tw_index
        FROM cycle_projections cp
        JOIN instruments i ON i.instrument_id = cp.instrument_id
        WHERE cp.k = 0
            AND cp.active = 1
            AND i.role = 'CANONICAL'{symbol_filter}
    """
    cursor.execute(query, params)
    for row in cursor.fetchall():
        symbol, tf, version, td_idx, tw_idx = row
        if tf == 'DAILY' and td_idx is None:
            errors.append(
                f"{symbol} DAILY v{version}: median_td_index is NULL (must be set for DAILY)"
            )
        if tf == 'DAILY' and tw_idx is not None:
            errors.append(
                f"{symbol} DAILY v{version}: median_tw_index is set (must be NULL for DAILY)"
            )
        if tf == 'WEEKLY' and tw_idx is None:
            errors.append(
                f"{symbol} WEEKLY v{version}: median_tw_index is NULL (must be set for WEEKLY)"
            )
        if tf == 'WEEKLY' and td_idx is not None:
            errors.append(
                f"{symbol} WEEKLY v{version}: median_td_index is set (must be NULL for WEEKLY)"
            )

    # Raise if any errors
    if errors:
        error_msg = "\n".join([f"  - {e}" for e in errors])
        raise CycleValidationError(
            f"Cycle validation failed with {len(errors)} error(s):\n{error_msg}"
        )


def get_validation_summary(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Get validation summary (for reporting, doesn't raise).
    Returns dict with counts and any issues found.
    """
    cursor = conn.cursor()

    # Count specs and projections
    cursor.execute("""
        SELECT COUNT(*)
        FROM cycle_specs
        WHERE status = 'ACTIVE'
    """)
    active_specs = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM cycle_projections
        WHERE k = 0 AND active = 1
    """)
    active_projections = cursor.fetchone()[0]

    # Try validation
    try:
        validate_cycles(conn)
        validation_status = 'PASS'
        validation_errors = []
    except CycleValidationError as e:
        validation_status = 'FAIL'
        validation_errors = str(e).split('\n')

    return {
        'active_specs': active_specs,
        'active_projections': active_projections,
        'validation_status': validation_status,
        'validation_errors': validation_errors
    }
