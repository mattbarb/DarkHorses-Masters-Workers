"""
Position Parsing Utilities
Handles extraction and normalization of race result position data
"""

import re
from typing import Optional, Tuple
from decimal import Decimal, InvalidOperation


def parse_position(position_value) -> Optional[int]:
    """
    Parse position from various formats to INTEGER.

    Args:
        position_value: Position value from API (can be str, int, or None)

    Returns:
        INTEGER position or None for special cases

    Examples:
        "1" -> 1
        "2" -> 2
        "10" -> 10
        1 -> 1
        "F" -> None (fell)
        "U" -> None (unseated)
        "PU" -> None (pulled up)
        "BD" -> None (brought down)
        "Died as a 5" -> 5 (extract position at death)
        "DIED" -> None (died, no position given)
        None -> None
    """
    if position_value is None or position_value == '':
        return None

    # Handle special codes (non-finishers)
    special_codes = [
        'F',    # Fell
        'U',    # Unseated
        'PU',   # Pulled up
        'BD',   # Brought down
        'RO',   # Ran out
        'DSQ',  # Disqualified
        'VO',   # Void
        'RR',   # Refused to race
        'CO',   # Carried out
        'SU',   # Slipped up
        'UR',   # Unseated rider
        'DIED', # Died during race
    ]

    position_str = str(position_value).upper().strip()

    # Check for exact match of special codes
    if position_str in special_codes:
        return None

    # Check for special codes at start of string (e.g., "DIED AS A 5")
    for code in special_codes:
        if position_str.startswith(code):
            # For death cases like "Died as a 5", extract the number
            # but only if it contains "AS" indicating position at death
            if code == 'DIED' and ' AS ' in position_str:
                # Extract number after "AS" (e.g., "Died as a 5" -> 5)
                match = re.search(r'AS\s+(?:A\s+)?(\d+)', position_str)
                if match:
                    return int(match.group(1))
            # For other special codes, return None (non-finisher)
            return None

    # Try to extract numeric value
    # Handles: "1", "1st", "2nd", "3rd", "4th", etc.
    try:
        # First try direct integer conversion
        return int(position_value)
    except (ValueError, TypeError):
        pass

    # Try to extract first number from string
    try:
        match = re.search(r'\d+', position_str)
        if match:
            return int(match.group())
    except (ValueError, AttributeError):
        pass

    # Could not parse
    return None


def parse_distance_beaten(distance_value) -> Optional[str]:
    """
    Parse distance beaten to standardized string format.

    Args:
        distance_value: Distance beaten value from API ('btn' field)

    Returns:
        Standardized distance string or None

    Examples:
        "0" -> "0" (winner)
        ".5" -> "0.5L"
        "1.25" -> "1.25L"
        "4.75" -> "4.75L"
        "35" -> "35L"
        "" -> None
        None -> None

    Note:
        API returns distances as numeric strings (e.g., "0.5", "1.25")
        We append "L" (lengths) for clarity
    """
    if distance_value is None or distance_value == '':
        return None

    distance_str = str(distance_value).strip()

    # Winner has "0" distance
    if distance_str == "0" or distance_str == "0.0":
        return "0"

    # Try to parse as decimal
    try:
        # Convert to float first to handle strings like ".5"
        distance_float = float(distance_str)

        # Format nicely (remove trailing zeros)
        if distance_float == int(distance_float):
            return f"{int(distance_float)}L"
        else:
            return f"{distance_float}L"
    except (ValueError, InvalidOperation):
        # Return as-is if can't parse
        return distance_str if distance_str else None


def parse_prize_money(prize_value) -> Optional[float]:
    """
    Parse prize money to FLOAT format (for JSON serialization).

    Args:
        prize_value: Prize money value from API

    Returns:
        Float prize value or None

    Examples:
        "3245.08" -> 3245.08
        3245.08 -> 3245.08
        "" -> None
        None -> None
    """
    if prize_value is None or prize_value == '':
        return None

    try:
        # Remove any currency symbols or commas
        prize_str = str(prize_value).replace('£', '').replace('$', '').replace(',', '').strip()

        if not prize_str:
            return None

        # Convert to float (JSON serializable)
        return float(prize_str)
    except (ValueError, InvalidOperation):
        return None


def parse_starting_price(sp_value) -> Optional[str]:
    """
    Parse starting price/odds to string format.

    Args:
        sp_value: Starting price value from API

    Returns:
        Starting price string or None

    Examples:
        "9/4" -> "9/4"
        "13/8F" -> "13/8F"  (F = favorite)
        "7/2" -> "7/2"
        "" -> None
        None -> None

    Note:
        We store as string to preserve fractional format
        "F" suffix indicates favorite
    """
    if sp_value is None or sp_value == '':
        return None

    sp_str = str(sp_value).strip()

    return sp_str if sp_str else None


def extract_position_data(runner_dict: dict) -> dict:
    """
    Extract all position-related fields from a runner dictionary.

    Args:
        runner_dict: Runner data dictionary from API

    Returns:
        Dictionary with parsed position fields:
        {
            'position': int or None,
            'distance_beaten': str or None,
            'prize_won': float or None,
            'starting_price': str or None,
            'starting_price_decimal': float or None
        }

    Example:
        runner = {
            'horse': 'Create (IRE)',
            'position': '1',
            'btn': '0',
            'prize': '3245.08',
            'sp': '9/4',
            'sp_dec': 3.25
        }

        result = extract_position_data(runner)
        # {
        #     'position': 1,
        #     'distance_beaten': '0',
        #     'prize_won': 3245.08,
        #     'starting_price': '9/4',
        #     'starting_price_decimal': 3.25
        # }
    """
    return {
        'position': parse_position(runner_dict.get('position')),
        'distance_beaten': parse_distance_beaten(runner_dict.get('btn')),
        'prize_won': parse_prize_money(runner_dict.get('prize')),
        'starting_price': parse_starting_price(runner_dict.get('sp')),
        'starting_price_decimal': parse_decimal_field(runner_dict.get('sp_dec'))
    }


def is_winner(runner_dict: dict) -> bool:
    """
    Check if a runner won the race.

    Args:
        runner_dict: Runner data dictionary from API

    Returns:
        True if runner won (position == 1), False otherwise
    """
    position = parse_position(runner_dict.get('position'))
    return position == 1


def is_placed(runner_dict: dict, num_places: int = 3) -> bool:
    """
    Check if a runner placed in the race.

    Args:
        runner_dict: Runner data dictionary from API
        num_places: Number of places (default 3)

    Returns:
        True if runner placed, False otherwise
    """
    position = parse_position(runner_dict.get('position'))
    return position is not None and position <= num_places


def did_not_finish(runner_dict: dict) -> bool:
    """
    Check if a runner did not finish (fell, pulled up, etc.).

    Args:
        runner_dict: Runner data dictionary from API

    Returns:
        True if runner did not finish, False otherwise
    """
    position_raw = runner_dict.get('position')
    if position_raw is None:
        return False

    # If position_raw is a special code, parse_position returns None
    # But position_raw itself is not None or empty
    position_parsed = parse_position(position_raw)

    return position_raw != '' and position_parsed is None


def parse_rating(rating_value) -> Optional[int]:
    """
    Parse rating fields (rpr, tsr, or/official_rating) to INTEGER.

    API returns "–" (en-dash) for missing/unavailable ratings.
    This function safely converts to None for database insertion.

    Args:
        rating_value: Rating value from API (can be str, int, or None)

    Returns:
        INTEGER rating or None if missing/invalid

    Examples:
        "66" -> 66
        66 -> 66
        "–" -> None (missing rating)
        "" -> None
        None -> None
    """
    if rating_value is None or rating_value == '':
        return None

    # Handle en-dash (–) and other missing indicators
    rating_str = str(rating_value).strip()
    if rating_str in ['–', '-', 'N/A', 'n/a']:
        return None

    # Try to convert to integer
    try:
        return int(rating_str)
    except (ValueError, TypeError):
        return None


def parse_int_field(value) -> Optional[int]:
    """
    Safely parse any integer field from API, handling empty strings and invalid values.

    Use this for fields like age, draw, number, weight_lbs, etc.

    Args:
        value: Value from API (can be str, int, or None)

    Returns:
        INTEGER value or None if missing/invalid

    Examples:
        "5" -> 5
        5 -> 5
        "" -> None (empty string)
        None -> None
        "abc" -> None (invalid)
    """
    if value is None or value == '':
        return None

    value_str = str(value).strip()
    if not value_str:
        return None

    try:
        return int(value_str)
    except (ValueError, TypeError):
        return None


def parse_decimal_field(value) -> Optional[float]:
    """
    Safely parse decimal/float field from API, handling empty strings and invalid values.

    Use this for fields like sp_dec, ovr_btn, btn (beaten distance), margin, etc.
    Handles special Racing API formats like "1L" (1 length), "0.5L", "-" (no value).

    Args:
        value: Value from API (can be str, float, or None)

    Returns:
        FLOAT value or None if missing/invalid

    Examples:
        "4.50" -> 4.50
        4.50 -> 4.50
        "1L" -> 1.0 (lengths notation)
        "0.5L" -> 0.5
        "14L" -> 14.0
        "-" -> None (missing value placeholder)
        "" -> None (empty string)
        None -> None
        "abc" -> None (invalid)
    """
    if value is None or value == '':
        return None

    value_str = str(value).strip()
    if not value_str or value_str == '-':  # "-" is used as placeholder for missing values
        return None

    # Handle "L" suffix (lengths notation, e.g., "1L", "0.5L")
    if value_str.endswith('L'):
        value_str = value_str[:-1].strip()
        if not value_str:
            return None

    try:
        return float(value_str)
    except (ValueError, TypeError):
        return None


def parse_text_field(value) -> Optional[str]:
    """
    Safely parse text field from API, handling None and empty strings.

    Use this for fields like comment, silk_url, weight (stones-lbs format), etc.

    Args:
        value: Value from API (can be str or None)

    Returns:
        STRING value or None if missing/empty

    Examples:
        "Led - ridden 2f out" -> "Led - ridden 2f out"
        "" -> None (empty string)
        None -> None
        "  " -> None (whitespace only)
    """
    if value is None:
        return None

    value_str = str(value).strip()
    return value_str if value_str else None
