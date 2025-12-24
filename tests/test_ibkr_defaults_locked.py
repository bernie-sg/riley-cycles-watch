"""
Guardrail test: Verify IBKR defaults are locked to 192.168.0.18:7496

This test ensures:
1. ibkr_config.py defaults are correct
2. No runtime code contains forbidden defaults (localhost, 127.0.0.1, 4002, 7497)
3. CLI scripts use correct defaults
"""
import os
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from riley.ibkr_config import DEFAULT_IBKR_HOST, DEFAULT_IBKR_PORT, get_ibkr_host, get_ibkr_port


def test_config_defaults():
    """Verify ibkr_config.py has correct defaults"""
    assert DEFAULT_IBKR_HOST == "192.168.0.18", \
        f"DEFAULT_IBKR_HOST must be '192.168.0.18', got '{DEFAULT_IBKR_HOST}'"
    assert DEFAULT_IBKR_PORT == 7496, \
        f"DEFAULT_IBKR_PORT must be 7496, got {DEFAULT_IBKR_PORT}"


def test_config_getters():
    """Verify config getters return correct defaults"""
    # Clear env vars to test defaults
    os.environ.pop('IBKR_HOST', None)
    os.environ.pop('IBKR_PORT', None)

    assert get_ibkr_host() == "192.168.0.18", \
        f"get_ibkr_host() must return '192.168.0.18', got '{get_ibkr_host()}'"
    assert get_ibkr_port() == 7496, \
        f"get_ibkr_port() must return 7496, got {get_ibkr_port()}"


def test_config_env_override():
    """Verify environment variables can override defaults"""
    os.environ['IBKR_HOST'] = '127.0.0.1'
    os.environ['IBKR_PORT'] = '4002'

    assert get_ibkr_host() == '127.0.0.1'
    assert get_ibkr_port() == 4002

    # Clean up
    os.environ.pop('IBKR_HOST')
    os.environ.pop('IBKR_PORT')


def test_no_forbidden_defaults_in_code():
    """Verify no Python files contain forbidden IBKR defaults"""
    forbidden_patterns = [
        ('7497', 'paper trading port'),
        ('4002', 'IB Gateway port'),
        ('127.0.0.1', 'localhost IP'),
        ('"localhost"', 'localhost string'),
        ("'localhost'", 'localhost string'),
    ]

    # Check all Python files in src/riley and scripts/
    search_paths = [
        project_root / "src" / "riley",
        project_root / "scripts",
    ]

    violations = []

    for search_path in search_paths:
        for py_file in search_path.rglob("*.py"):
            content = py_file.read_text()

            for pattern, description in forbidden_patterns:
                if pattern in content:
                    # Skip if it's just a comment or in this test file
                    if py_file.name == "test_ibkr_defaults_locked.py":
                        continue

                    # Find line number
                    for i, line in enumerate(content.split('\n'), 1):
                        if pattern in line and not line.strip().startswith('#'):
                            violations.append(
                                f"{py_file.relative_to(project_root)}:{i} contains {description} ({pattern})"
                            )

    assert len(violations) == 0, \
        f"Found forbidden IBKR defaults in code:\n" + "\n".join(violations)


def test_cli_defaults():
    """Verify CLI scripts have correct argument defaults"""
    riley_run_one = project_root / "scripts" / "riley_run_one.py"

    if riley_run_one.exists():
        content = riley_run_one.read_text()

        # Check --host default
        assert "default='192.168.0.18'" in content or 'default="192.168.0.18"' in content, \
            "riley_run_one.py --host default must be '192.168.0.18'"

        # Check --port default
        assert "default=7496" in content, \
            "riley_run_one.py --port default must be 7496"

        # Ensure no --live or --paper flags exist
        assert "--live" not in content or "action='store_true'" not in content, \
            "riley_run_one.py should not have --live flag"


if __name__ == '__main__':
    print("Running IBKR defaults guardrail tests...\n")

    try:
        test_config_defaults()
        print("✓ Config defaults are correct")

        test_config_getters()
        print("✓ Config getters work correctly")

        test_config_env_override()
        print("✓ Environment variable overrides work")

        test_no_forbidden_defaults_in_code()
        print("✓ No forbidden defaults in code")

        test_cli_defaults()
        print("✓ CLI defaults are correct")

        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED - IBKR defaults are locked to 192.168.0.18:7496")
        print("="*60)

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
