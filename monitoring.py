"""
Memory monitoring and cleanup utilities for GayATCU dashboard.

Provides resource tracking and cache eviction functions to optimize
performance on Streamlit Community Cloud (2.7GB memory limit).
"""

import gc
import logging

# Try to import psutil with graceful degradation for Streamlit Cloud compatibility
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logging.warning("⚠️ psutil not available - memory monitoring disabled")

import streamlit as st

logger = logging.getLogger(__name__)


def monitor_memory_usage() -> None:
    """
    Monitor and display memory usage in the sidebar.

    Shows current memory usage and warns if approaching the 2GB limit
    (Community Cloud has a 2.7GB maximum, warn at 2GB for safety).

    Only functions if psutil is available. Falls back gracefully otherwise.
    """
    if not HAS_PSUTIL:
        if st.sidebar:
            st.sidebar.caption("💾 Memory monitoring unavailable")
        return

    try:
        process = psutil.Process()
        mem_info = process.memory_info()
        mem_mb = mem_info.rss / 1024 / 1024

        # Display memory usage in sidebar
        st.sidebar.metric(
            "💾 Memory Usage",
            f"{mem_mb:.1f} MB",
            help="Current process memory usage (Community Cloud limit: 2.7GB)"
        )

        # Warn if approaching limit
        if mem_mb > 2048:  # 2GB warning threshold
            st.sidebar.warning(
                "⚠️ Approaching memory limit! "
                "Consider clearing cache or restarting."
            )
            logger.warning(f"Memory usage high: {mem_mb:.1f} MB")

    except Exception as e:
        logger.error(f"Error monitoring memory: {e}")
        st.sidebar.caption("💾 Memory monitoring error")


def cleanup_session_state() -> None:
    """
    Clean up unused session state entries to prevent memory leaks.

    Removes old cache entries and forces garbage collection.
    This helps maintain memory usage within Community Cloud limits.

    Safe to call even if psutil is unavailable.
    """
    try:
        if not hasattr(st, 'session_state'):
            return

        # Remove old cache entries (limit cleanup to 10 entries per call)
        keys_to_remove = []
        for key in st.session_state.keys():
            if key.startswith('_cache_data_'):
                keys_to_remove.append(key)

        cleaned_count = 0
        for key in keys_to_remove[:10]:  # Limit cleanup to prevent performance impact
            try:
                del st.session_state[key]
                cleaned_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete cache key {key}: {e}")

        if cleaned_count > 0:
            logger.info(f"Cleaned {cleaned_count} cache entries")

        # Force garbage collection
        gc.collect()

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


def get_memory_info() -> dict:
    """
    Get detailed memory information if psutil is available.

    Returns:
        dict: Memory stats including RSS, VMS, and percentage
              Returns empty dict if psutil unavailable
    """
    if not HAS_PSUTIL:
        return {}

    try:
        process = psutil.Process()
        mem_info = process.memory_info()

        return {
            "rss_mb": mem_info.rss / 1024 / 1024,
            "vms_mb": mem_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
            "available": True
        }
    except Exception as e:
        logger.error(f"Error getting memory info: {e}")
        return {"available": False}


def check_memory_threshold(threshold_mb: float = 2048) -> bool:
    """
    Check if memory usage exceeds the given threshold.

    Args:
        threshold_mb: Memory threshold in MB (default: 2048 MB = 2GB)

    Returns:
        bool: True if memory exceeds threshold, False otherwise or if psutil unavailable
    """
    if not HAS_PSUTIL:
        return False

    try:
        mem_info = get_memory_info()
        if mem_info.get("available", False):
            return mem_info["rss_mb"] > threshold_mb
    except Exception as e:
        logger.error(f"Error checking memory threshold: {e}")

    return False
