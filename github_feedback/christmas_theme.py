"""Christmas theme for CLI - Active from November 1st to December 31st."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.theme import Theme


def is_christmas_season() -> bool:
    """Check if current date is in Christmas season (November 1 - December 31)."""
    now = datetime.now()
    return now.month in (11, 12)


def get_christmas_theme() -> Theme:
    """Get Christmas-themed color scheme with red and green colors."""
    from rich.theme import Theme

    return Theme(
        {
            # Christmas red and green color scheme
            "accent": "bold rgb(220,38,38)",  # Christmas red
            "muted": "dim rgb(187,247,208)",  # Light green
            "title": "bold rgb(250,204,21)",  # Gold
            "repo": "bold italic rgb(74,222,128)",  # Bright green
            "label": "bold rgb(134,239,172)",  # Light green
            "value": "rgb(254,242,242)",  # Snow white
            "success": "bold rgb(22,163,74)",  # Christmas green
            "warning": "bold rgb(250,204,21)",  # Gold
            "danger": "bold rgb(220,38,38)",  # Christmas red
            "divider": "rgb(153,27,27)",  # Dark red
            "frame": "rgb(22,163,74)",  # Christmas green
        }
    )


def get_christmas_tree() -> str:
    """Return a colorful Christmas tree ASCII art."""
    return """[rgb(250,204,21)]    ★[/]
[rgb(22,163,74)]    /\\[/]
[rgb(22,163,74)]   /[rgb(220,38,38)]o[rgb(22,163,74)]\\[/]
[rgb(22,163,74)]  /[rgb(250,204,21)]o[rgb(22,163,74)]  \\[/]
[rgb(22,163,74)] /[rgb(220,38,38)]o[rgb(22,163,74)] [rgb(250,204,21)]o[rgb(22,163,74)] \\[/]
[rgb(22,163,74)]/[rgb(220,38,38)]o[rgb(22,163,74)] [rgb(250,204,21)]o[rgb(22,163,74)] [rgb(220,38,38)]o[rgb(22,163,74)]\\[/]
[rgb(101,67,33)]   |||[/]"""


def get_snowman() -> str:
    """Return a cute snowman ASCII art."""
    return """[rgb(255,255,255)]  ☃️  [/]
[rgb(74,222,128)]⛄ Happy Holidays! ⛄[/]"""


def get_reindeer() -> str:
    """Return Rudolph the reindeer ASCII art."""
    return """[rgb(101,67,33)]  }   {[/]
[rgb(101,67,33)]  (o.o)[/]
[rgb(101,67,33)]   > [rgb(220,38,38)]♥[rgb(101,67,33)] <[/]"""


def get_christmas_decorations() -> str:
    """Return a festive decoration banner."""
    snow_line = "[rgb(255,255,255)]" + "❄ " * 20 + "[/]"
    festive_line = "[rgb(220,38,38)]🎄[/] [rgb(22,163,74)]Merry Christmas![/] [rgb(220,38,38)]🎄[/] [rgb(250,204,21)]✨[/] [rgb(22,163,74)]Happy Holidays![/] [rgb(250,204,21)]✨[/] [rgb(220,38,38)]🎁[/]"

    return f"{snow_line}\n{festive_line}\n{snow_line}"


def get_christmas_banner() -> str:
    """Return a full Christmas banner with tree, snowman, and decorations."""
    tree = get_christmas_tree()
    decorations = get_christmas_decorations()

    return f"\n{decorations}\n\n{tree}\n"


def get_festive_message() -> str:
    """Return a random festive message."""
    import random

    messages = [
        "[rgb(220,38,38)]🎅[/] [rgb(22,163,74)]Ho Ho Ho! Analyzing your feedback...[/]",
        "[rgb(255,255,255)]❄️[/] [rgb(74,222,128)]'Tis the season for retrospectives![/]",
        "[rgb(250,204,21)]⭐[/] [rgb(22,163,74)]Spreading festive cheer and code reviews![/]",
        "[rgb(220,38,38)]🎁[/] [rgb(74,222,128)]Unwrapping your GitHub insights...[/]",
        "[rgb(22,163,74)]🎄[/] [rgb(220,38,38)]May your builds be merry and your tests be bright![/]",
    ]

    return random.choice(messages)


__all__ = [
    "is_christmas_season",
    "get_christmas_theme",
    "get_christmas_tree",
    "get_snowman",
    "get_reindeer",
    "get_christmas_decorations",
    "get_christmas_banner",
    "get_festive_message",
]
