"""
parsing.py
-----------

Utility functions for parsing environment variables and other string-based settings.

Includes a helper to parse comma-separated lists from environment variables
into clean Python lists, with whitespace stripped and empty entries ignored.

Example usage:

    import os
    from parsing import parse_env_list

    # Suppose your .env file has:
    # ALLOWED_ORIGINS=http://localhost:3000,https://example.com
    origins_str = os.getenv("ALLOWED_ORIGINS", "")
    ALLOWED_ORIGINS = parse_env_list(origins_str)
    # ALLOWED_ORIGINS -> ["http://localhost:3000", "https://example.com"]

    # Empty string results in an empty list
    parse_env_list("")  # -> []
"""

from typing import List


def parse_env_list(env_value: str) -> List[str]:
    """
    Parse a comma-separated string into a list of non-empty, stripped strings.

    Leading and trailing whitespace is removed from each item.
    Empty entries are ignored.

    Args:
        env_value (str): The comma-separated string to parse.

    Returns:
        List[str]: A list of cleaned strings.

    Examples:
        >>> parse_env_list("a,b,c")
        ['a', 'b', 'c']

        >>> parse_env_list("  apple , banana , cherry ")
        ['apple', 'banana', 'cherry']

        >>> parse_env_list(",,,apple,, ,banana,,")
        ['apple', 'banana']

        >>> parse_env_list("")
        []

        >>> parse_env_list(None)
        []
    """
    if not env_value:
        return []
    # Split by comma, strip whitespace, and ignore empty strings
    return [item.strip() for item in env_value.split(",") if item.strip()]
