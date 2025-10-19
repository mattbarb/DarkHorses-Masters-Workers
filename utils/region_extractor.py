"""
Region Extractor Utility
Extracts breeding region from horse names

Horse names often include country codes indicating breeding origin:
- "Afternoon Delight (IRE)" → Ireland
- "Natavia (GB)" → Great Britain
- "Seattle Slew (USA)" → USA
"""

import re
from typing import Optional


# Map of country codes to regions
COUNTRY_CODE_MAP = {
    # UK & Ireland (our primary focus)
    'IRE': 'ire',  # Ireland
    'GB': 'gb',    # Great Britain
    'UK': 'gb',    # United Kingdom (alias for GB)

    # Other common regions
    'FR': 'fr',    # France
    'USA': 'usa',  # United States
    'GER': 'ger',  # Germany
    'AUS': 'aus',  # Australia
    'NZ': 'nz',    # New Zealand
    'SAF': 'saf',  # South Africa
    'JPN': 'jpn',  # Japan
    'ITY': 'ity',  # Italy
    'SPA': 'spa',  # Spain
}


def extract_region_from_name(horse_name: str) -> Optional[str]:
    """
    Extract breeding region from horse name

    Args:
        horse_name: Horse name, possibly with country code like "Horse Name (IRE)"

    Returns:
        Region code (lowercase) or None if no region found

    Examples:
        >>> extract_region_from_name("Afternoon Delight (IRE)")
        'ire'
        >>> extract_region_from_name("Natavia (GB)")
        'gb'
        >>> extract_region_from_name("Plain Horse Name")
        None
    """
    if not horse_name:
        return None

    # Look for country code in parentheses at end of name
    match = re.search(r'\(([A-Z]{2,3})\)\s*$', horse_name)

    if match:
        country_code = match.group(1)
        return COUNTRY_CODE_MAP.get(country_code, country_code.lower())

    return None


def extract_region_with_fallback(horse_name: str, fallback: str = None) -> Optional[str]:
    """
    Extract breeding region with fallback

    Args:
        horse_name: Horse name to extract from
        fallback: Fallback region if extraction fails

    Returns:
        Extracted region, fallback, or None
    """
    region = extract_region_from_name(horse_name)
    return region if region else fallback


# For testing
if __name__ == '__main__':
    test_cases = [
        "Afternoon Delight (IRE)",
        "Natavia (GB)",
        "Seattle Slew (USA)",
        "Plain Horse Name",
        "Dubawi (IRE)",
        "Frankel (GB)",
    ]

    print("Testing region extraction:")
    print("=" * 60)
    for name in test_cases:
        region = extract_region_from_name(name)
        print(f"{name:30} → {region}")
