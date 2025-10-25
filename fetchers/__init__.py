"""Fetchers package - Data collection from Racing API"""

# Core API Fetchers (Legacy - Active)
from .bookmakers_fetcher import BookmakersFetcher
from .courses_fetcher import CoursesFetcher
from .horses_fetcher import HorsesFetcher
from .races_fetcher import RacesFetcher
from .results_fetcher import ResultsFetcher

# New Consolidated Fetchers (Recommended)
from .events_fetcher import EventsFetcher
from .masters_fetcher import MastersFetcher

# Statistics Wrapper
from .statistics_fetcher import StatisticsFetcher

# Note: JockeysFetcher, TrainersFetcher, OwnersFetcher moved to _deprecated/
# These fetchers have known API issues (require 'name' parameter)
# Use entity extraction instead (automatic in RacesFetcher/ResultsFetcher)

__all__ = [
    # Legacy fetchers (active)
    'BookmakersFetcher',
    'CoursesFetcher',
    'HorsesFetcher',
    'RacesFetcher',
    'ResultsFetcher',
    # New consolidated fetchers (recommended)
    'EventsFetcher',
    'MastersFetcher',
    # Utilities
    'StatisticsFetcher',
]
