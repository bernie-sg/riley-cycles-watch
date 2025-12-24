"""IBKR connection configuration - single source of truth"""
import os

DEFAULT_IBKR_HOST = "192.168.0.18"
DEFAULT_IBKR_PORT = 7496


def get_ibkr_host() -> str:
    """Get IBKR host (env override or default)"""
    return os.getenv("IBKR_HOST", DEFAULT_IBKR_HOST)


def get_ibkr_port() -> int:
    """Get IBKR port (env override or default)"""
    v = os.getenv("IBKR_PORT")
    return int(v) if v else DEFAULT_IBKR_PORT
