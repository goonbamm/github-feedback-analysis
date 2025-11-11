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
    return """[rgb(250,204,21) bold]         ✦[/]
[rgb(22,163,74)]        /[rgb(250,204,21)]★[rgb(22,163,74)]\\[/]
[rgb(22,163,74)]       /[rgb(220,38,38)]●[rgb(22,163,74)] [rgb(255,255,255)]◦[rgb(22,163,74)]\\[/]
[rgb(22,163,74)]      /[rgb(250,204,21)]●[rgb(22,163,74)]   [rgb(220,38,38)]●[rgb(22,163,74)]\\[/]
[rgb(22,163,74)]     /[rgb(220,38,38)]◦[rgb(22,163,74)] [rgb(250,204,21)]✦[rgb(22,163,74)] [rgb(220,38,38)]●[rgb(22,163,74)] [rgb(255,255,255)]◦[rgb(22,163,74)]\\[/]
[rgb(22,163,74)]    /[rgb(250,204,21)]●[rgb(22,163,74)]   [rgb(220,38,38)]◦[rgb(22,163,74)]   [rgb(250,204,21)]●[rgb(22,163,74)]\\[/]
[rgb(22,163,74)]   /[rgb(220,38,38)]◦[rgb(22,163,74)] [rgb(255,255,255)]●[rgb(22,163,74)] [rgb(250,204,21)]●[rgb(22,163,74)] [rgb(220,38,38)]●[rgb(22,163,74)] [rgb(255,255,255)]◦[rgb(22,163,74)]\\[/]
[rgb(22,163,74)]  /[rgb(250,204,21)]●[rgb(22,163,74)]   [rgb(220,38,38)]◦[rgb(22,163,74)] [rgb(250,204,21)]✦[rgb(22,163,74)] [rgb(220,38,38)]◦[rgb(22,163,74)]   [rgb(250,204,21)]●[rgb(22,163,74)]\\[/]
[rgb(22,163,74)] /[rgb(220,38,38)]◦[rgb(22,163,74)] [rgb(255,255,255)]●[rgb(22,163,74)] [rgb(250,204,21)]●[rgb(22,163,74)] [rgb(220,38,38)]●[rgb(22,163,74)] [rgb(255,255,255)]◦[rgb(22,163,74)] [rgb(220,38,38)]●[rgb(22,163,74)] [rgb(250,204,21)]●[rgb(22,163,74)]\\[/]
[rgb(101,67,33) bold]      ║║║[/]
[rgb(101,67,33) bold]      ║║║[/]"""


def get_snowman() -> str:
    """Return a cute snowman ASCII art."""
    return """[rgb(255,255,255) bold]     _[rgb(220,38,38)]^[rgb(255,255,255)]_[/]
[rgb(255,255,255) bold]    ([rgb(0,0,0)]• •[rgb(255,255,255)])[/]
[rgb(255,255,255) bold]    ([rgb(255,140,0)]▬[rgb(255,255,255)])[/]
[rgb(255,255,255) bold]   ([rgb(220,38,38)]● ● ●[rgb(255,255,255)])[/]
[rgb(255,255,255) bold]  ([rgb(220,38,38)]● ● ● ●[rgb(255,255,255)])[/]
[rgb(101,67,33)]  [rgb(255,255,255)]╚[rgb(101,67,33)]═[rgb(255,255,255)]╝ [rgb(255,255,255)]╚[rgb(101,67,33)]═[rgb(255,255,255)]╝[/]"""


def get_reindeer() -> str:
    """Return Rudolph the reindeer ASCII art."""
    return """[rgb(139,69,19) bold]    ╱|╲   ╱|╲[/]
[rgb(139,69,19) bold]   (⟡[rgb(220,38,38)]◉[rgb(139,69,19)]⟡)[/]
[rgb(139,69,19) bold]    ╰─[rgb(220,38,38) bold blink]●[rgb(139,69,19) bold]─╯[/]
[rgb(139,69,19) bold]     │││[/]
[rgb(250,204,21)]   ～ Rudolph ～[/]"""


def get_christmas_decorations() -> str:
    """Return a festive decoration banner."""
    snow_line = "[rgb(135,206,250)]╔" + "═" * 78 + "╗[/]"
    snow_top = "[rgb(255,255,255) bold]" + " ❄ " * 26 + "[/]"
    festive_line = "[rgb(220,38,38) bold]  🎄[/] [rgb(22,163,74) bold]Merry Christmas![/] [rgb(220,38,38) bold]🎄[/] [rgb(250,204,21) bold]✨[/] [rgb(22,163,74) bold]Happy Holidays![/] [rgb(250,204,21) bold]✨[/] [rgb(220,38,38) bold]🎁[/] [rgb(135,206,250)]Season's Greetings![/] [rgb(250,204,21)]⭐[/]"
    snow_bottom = "[rgb(135,206,250)]╚" + "═" * 78 + "╝[/]"

    return f"{snow_line}\n{snow_top}\n{festive_line}\n{snow_top}\n{snow_bottom}"


def get_christmas_banner() -> str:
    """Return a full Christmas banner with tree, snowman, and decorations."""
    decorations = get_christmas_decorations()
    tree = get_christmas_tree()
    gifts = get_gift_boxes()

    return f"\n{decorations}\n\n{tree}\n\n{gifts}\n"


def get_gift_boxes() -> str:
    """Return colorful gift boxes ASCII art."""
    return """[rgb(220,38,38) bold]      ╔═══╗[/]  [rgb(22,163,74) bold]╔═══╗[/]  [rgb(250,204,21) bold]╔═══╗[/]
[rgb(220,38,38) bold]      ║[rgb(250,204,21)]🎀[rgb(220,38,38)]║[/]  [rgb(22,163,74) bold]║[rgb(220,38,38)]🎀[rgb(22,163,74)]║[/]  [rgb(250,204,21) bold]║[rgb(220,38,38)]🎀[rgb(250,204,21)]║[/]
[rgb(220,38,38) bold]      ╚═══╝[/]  [rgb(22,163,74) bold]╚═══╝[/]  [rgb(250,204,21) bold]╚═══╝[/]"""


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
    "get_gift_boxes",
    "get_festive_message",
]
