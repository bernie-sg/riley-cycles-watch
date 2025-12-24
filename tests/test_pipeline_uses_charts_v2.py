"""Test that pipeline uses charts_v2 and not old charts module"""
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def test_riley_run_one_imports_charts_v2():
    """Test that riley_run_one.py imports charts_v2"""
    riley_run_one_path = project_root / "scripts" / "riley_run_one.py"
    content = riley_run_one_path.read_text()

    # Check that charts_v2 is imported
    assert 'from riley.charts_v2 import render_daily_weekly' in content, \
        "riley_run_one.py must import render_daily_weekly from charts_v2"

    # Check that render_daily_weekly is called
    assert 'render_daily_weekly(' in content, \
        "riley_run_one.py must call render_daily_weekly"

    print("✓ riley_run_one.py imports and uses charts_v2")


def test_riley_run_one_imports_weekly_v2():
    """Test that riley_run_one.py imports weekly_v2"""
    riley_run_one_path = project_root / "scripts" / "riley_run_one.py"
    content = riley_run_one_path.read_text()

    # Check that weekly_v2 is imported
    assert 'from riley.weekly_v2 import make_weekly_from_daily' in content, \
        "riley_run_one.py must import make_weekly_from_daily from weekly_v2"

    # Check that make_weekly_from_daily is called
    assert 'make_weekly_from_daily(' in content, \
        "riley_run_one.py must call make_weekly_from_daily"

    print("✓ riley_run_one.py imports and uses weekly_v2")


def test_riley_run_one_imports_validate_v2():
    """Test that riley_run_one.py imports validate_v2"""
    riley_run_one_path = project_root / "scripts" / "riley_run_one.py"
    content = riley_run_one_path.read_text()

    # Check that validate_v2 is imported
    assert 'from riley.validate_v2 import validate_daily, validate_weekly' in content, \
        "riley_run_one.py must import validate_daily and validate_weekly from validate_v2"

    # Check that validation is called
    assert 'validate_daily(' in content, \
        "riley_run_one.py must call validate_daily"
    assert 'validate_weekly(' in content, \
        "riley_run_one.py must call validate_weekly"

    print("✓ riley_run_one.py imports and uses validate_v2")


if __name__ == '__main__':
    test_riley_run_one_imports_charts_v2()
    test_riley_run_one_imports_weekly_v2()
    test_riley_run_one_imports_validate_v2()
    print("\n✓ All pipeline integration tests passed")
