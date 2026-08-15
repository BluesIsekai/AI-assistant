import os
import gc
import tracemalloc

_tracker_enabled = os.environ.get("ENABLE_MEMORY_TRACKER", "0").lower() in ("1", "true", "yes")


def init_memory_tracker() -> None:
    """Initializes tracemalloc if ENABLE_MEMORY_TRACKER environment variable is set."""
    if _tracker_enabled and not tracemalloc.is_tracing():
        tracemalloc.start()
        print("📊 [Memory Tracker] Active.")


def print_memory_stats(top_n: int = 5) -> None:
    """Logs current memory allocation and top allocation lines if memory tracker is enabled."""
    if not _tracker_enabled or not tracemalloc.is_tracing():
        return

    gc.collect()
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")

    current, peak = tracemalloc.get_traced_memory()
    print("\n📊 [Memory Tracker Stats]")
    print(f"   Current RAM allocated: {current / (1024 * 1024):.2f} MB")
    print(f"   Peak RAM allocated:    {peak / (1024 * 1024):.2f} MB")
    print(f"   Top {top_n} allocation sources:")
    for stat in top_stats[:top_n]:
        print(f"     - {stat}")
    print()
