"""Year-in-review report sections."""

from .character_stats import generate_character_stats
from .communication_section import generate_communication_skills_section
from .executive_summary import generate_executive_summary
from .goals_section import generate_footer, generate_goals_section
from .header_section import generate_header
from .repository_breakdown import generate_repository_breakdown
from .tech_stack_section import generate_tech_stack_analysis

__all__ = [
    "generate_header",
    "generate_executive_summary",
    "generate_repository_breakdown",
    "generate_tech_stack_analysis",
    "generate_character_stats",
    "generate_communication_skills_section",
    "generate_goals_section",
    "generate_footer",
]
