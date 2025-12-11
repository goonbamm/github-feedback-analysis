#!/usr/bin/env python3
"""
Systematic import fixer for github-feedback-analysis codebase.

This script fixes all incorrect import statements in the codebase:
1. Fixes collector imports (from .collector -> from ..collectors.collector)
2. Fixes core module imports (from ..X -> from ..core.X where appropriate)
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path("/home/user/github-feedback-analysis")


def read_file(file_path: Path) -> str:
    """Read file contents."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(file_path: Path, content: str) -> None:
    """Write content to file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def fix_collector_imports(content: str, file_path: Path) -> Tuple[str, List[str]]:
    """
    Fix collector imports.

    Changes:
    - from .collector import Collector -> from ..collectors.collector import Collector (in cli/)
    - from .collector import Collector -> from .collectors.collector import Collector (in root)
    """
    changes = []

    # Check if file is in cli directory
    is_cli_file = 'github_feedback/cli/' in str(file_path)
    is_root_file = str(file_path).count('/') == str(get_project_root() / 'github_feedback').count('/') + 1

    pattern = r'from \.collector import Collector'

    if re.search(pattern, content):
        if is_cli_file:
            new_import = 'from ..collectors.collector import Collector'
        else:
            new_import = 'from .collectors.collector import Collector'

        old_content = content
        content = re.sub(pattern, new_import, content)

        if old_content != content:
            changes.append(f"  ✓ Fixed collector import: {pattern} -> {new_import}")

    return content, changes


def fix_core_module_imports(content: str, file_path: Path) -> Tuple[str, List[str]]:
    """
    Fix core module imports.

    Changes imports from ..X to ..core.X for:
    - constants, models, console, utils, prompts

    Also handles ... (triple dot) imports from subdirectories

    Exceptions:
    - game_elements/renderers/* can import from ..constants (game_elements.constants)
    - Files already importing from ..core.* are skipped
    """
    changes = []

    # Determine if this file should skip certain fixes
    is_game_renderer = 'github_feedback/game_elements/renderers/' in str(file_path)
    is_year_in_review = 'github_feedback/year_in_review/' in str(file_path)

    # Map of old imports to new imports
    # Only fix these if they're NOT already importing from ..core.X
    core_modules = {
        'constants': 'core.constants',
        'models': 'core.models',
        'console': 'core.console',
        'utils': 'core.utils',
    }

    for old_module, new_module in core_modules.items():
        # Skip constants for game renderers (they have their own constants)
        if old_module == 'constants' and is_game_renderer:
            continue

        # Pattern to match imports like: from ..constants import X
        # But not: from ..core.constants import X or from ..game_elements.constants
        pattern = rf'from \.\.{old_module} import'

        if re.search(pattern, content):
            new_import_path = f'from ..{new_module} import'

            old_content = content
            content = re.sub(pattern, new_import_path, content)

            if old_content != content:
                changes.append(f"  ✓ Fixed {old_module} import: from ..{old_module} -> from ..{new_module}")

        # Also handle triple-dot imports (from ... directories)
        # e.g., from ...constants -> from ...core.constants
        pattern = rf'from \.\.\.{old_module} import'

        if re.search(pattern, content):
            new_import_path = f'from ...{new_module} import'

            old_content = content
            content = re.sub(pattern, new_import_path, content)

            if old_content != content:
                changes.append(f"  ✓ Fixed {old_module} import: from ...{old_module} -> from ...{new_module}")

    return content, changes


def fix_single_dot_core_imports(content: str, file_path: Path) -> Tuple[str, List[str]]:
    """
    Fix single-dot core module imports for files directly in subdirectories.

    Changes imports from .X to .core.X for files in review_reports, section_builders, etc.
    """
    changes = []

    # Determine which directory this file is in
    path_str = str(file_path)

    # Files in certain subdirectories that should import from core
    needs_core_prefix = (
        'github_feedback/review_reports/' in path_str or
        'github_feedback/section_builders/' in path_str or
        'github_feedback/retrospective_builders/' in path_str or
        'github_feedback/year_in_review/' in path_str
    )

    if not needs_core_prefix:
        return content, changes

    # For files in review_reports and similar, they import from parent
    # e.g., from ..console -> should be from ..core.console
    # This is already handled by fix_core_module_imports

    return content, changes


def fix_collector_module_imports(content: str, file_path: Path) -> Tuple[str, List[str]]:
    """
    Fix collector.py specific imports.

    Changes:
    - from .analytics_collector -> from .analytics
    - from .commit_collector -> from .commits
    - from .issue_collector -> from .issues
    - from .pr_collector -> from .prs
    - from .review_collector -> from .reviews
    - from .api_client -> from ..api.client
    - from .repository_manager -> from ..repository_manager
    """
    changes = []

    # Only fix collector.py
    if not str(file_path).endswith('collectors/collector.py'):
        return content, changes

    # Map of incorrect module names to correct ones
    collector_renames = {
        '.analytics_collector': '.analytics',
        '.commit_collector': '.commits',
        '.issue_collector': '.issues',
        '.pr_collector': '.prs',
        '.review_collector': '.reviews',
        '.api_client': '..api.client',
        '.repository_manager': '..repository_manager',
    }

    for old_import, new_import in collector_renames.items():
        pattern = rf'from {re.escape(old_import)} import'

        if re.search(pattern, content):
            new_import_statement = f'from {new_import} import'
            old_content = content
            content = re.sub(pattern, new_import_statement, content)

            if old_content != content:
                changes.append(f"  ✓ Fixed import: from {old_import} -> from {new_import}")

    return content, changes


def fix_all_collectors_imports(content: str, file_path: Path) -> Tuple[str, List[str]]:
    """
    Fix imports in all collector files (analytics.py, commits.py, etc.)

    Changes:
    - from .api_params -> from ..api.params
    - from .base_collector -> from .base
    - from .api_client -> from ..api.client
    - from .filters -> from ..filters
    """
    changes = []

    # Only fix files in collectors directory (except collector.py, handled elsewhere)
    if 'github_feedback/collectors/' not in str(file_path):
        return content, changes

    if str(file_path).endswith('collectors/collector.py'):
        return content, changes  # Already handled by fix_collector_module_imports

    # Map of incorrect imports to correct ones
    import_fixes = {
        '.api_params': '..api.params',
        '.base_collector': '.base',
        '.api_client': '..api.client',
        '.filters': '..filters',
    }

    for old_import, new_import in import_fixes.items():
        pattern = rf'from {re.escape(old_import)} import'

        if re.search(pattern, content):
            new_import_statement = f'from {new_import} import'
            old_content = content
            content = re.sub(pattern, new_import_statement, content)

            if old_content != content:
                changes.append(f"  ✓ Fixed import: from {old_import} -> from {new_import}")

    return content, changes


def fix_cli_analyzer_imports(content: str, file_path: Path) -> Tuple[str, List[str]]:
    """
    Fix analyzer imports in CLI files.

    Changes:
    - from .analyzer -> from ..analyzer (in cli files)
    """
    changes = []

    # Only fix files in cli directory
    if 'github_feedback/cli/' not in str(file_path):
        return content, changes

    pattern = r'from \.analyzer import'

    if re.search(pattern, content):
        new_import = 'from ..analyzer import'
        old_content = content
        content = re.sub(pattern, new_import, content)

        if old_content != content:
            changes.append(f"  ✓ Fixed analyzer import: from .analyzer -> from ..analyzer")

    return content, changes


def fix_cli_root_module_imports(content: str, file_path: Path) -> Tuple[str, List[str]]:
    """
    Fix imports in CLI files that reference root-level modules.

    Changes:
    - from .llm -> from ..llm (in cli files)
    - from .repository_manager -> from ..repository_manager (in cli files)
    - from .award_strategies -> from ..award_strategies (in cli files)
    - from .retrospective -> from ..retrospective (in cli files)
    - from .reviewer -> from ..reviewer (in cli files)
    - from .cli_helpers -> from .helpers (in cli files)
    """
    changes = []

    # Only fix files in cli directory
    if 'github_feedback/cli/' not in str(file_path):
        return content, changes

    # Modules that are in root github_feedback, not in cli
    root_modules = ['llm', 'repository_manager', 'award_strategies', 'retrospective', 'reviewer', 'prompts', 'repository_display']

    for module in root_modules:
        pattern = rf'from \.{module} import'

        if re.search(pattern, content):
            new_import = f'from ..{module} import'
            old_content = content
            content = re.sub(pattern, new_import, content)

            if old_content != content:
                changes.append(f"  ✓ Fixed {module} import: from .{module} -> from ..{module}")

    # Fix cli_helpers -> helpers
    pattern = r'from \.cli_helpers import'
    if re.search(pattern, content):
        new_import = 'from .helpers import'
        old_content = content
        content = re.sub(pattern, new_import, content)

        if old_content != content:
            changes.append(f"  ✓ Fixed cli_helpers import: from .cli_helpers -> from .helpers")

    # Fix year_in_review_reporter imports
    # Replace: from .year_in_review_reporter import YearInReviewReporter, RepositoryAnalysis
    # With: from ..year_in_review.reporter import YearInReviewReporter; from ..year_in_review.models import RepositoryAnalysis

    # First, handle the combined import
    pattern = r'from \.year_in_review_reporter import YearInReviewReporter, RepositoryAnalysis'
    if re.search(pattern, content):
        replacement = 'from ..year_in_review.reporter import YearInReviewReporter\n    from ..year_in_review.models import RepositoryAnalysis'
        old_content = content
        content = re.sub(pattern, replacement, content)
        if old_content != content:
            changes.append(f"  ✓ Fixed year_in_review_reporter import (combined)")

    # Handle individual imports
    pattern = r'from \.year_in_review_reporter import RepositoryAnalysis'
    if re.search(pattern, content):
        replacement = 'from ..year_in_review.models import RepositoryAnalysis'
        old_content = content
        content = re.sub(pattern, replacement, content)
        if old_content != content:
            changes.append(f"  ✓ Fixed year_in_review_reporter import (RepositoryAnalysis)")

    pattern = r'from \.year_in_review_reporter import YearInReviewReporter'
    if re.search(pattern, content):
        replacement = 'from ..year_in_review.reporter import YearInReviewReporter'
        old_content = content
        content = re.sub(pattern, replacement, content)
        if old_content != content:
            changes.append(f"  ✓ Fixed year_in_review_reporter import (YearInReviewReporter)")

    # Fix reporter import
    pattern = r'from \.reporter import Reporter'
    if re.search(pattern, content):
        replacement = 'from ..reporters.reporter import Reporter'
        old_content = content
        content = re.sub(pattern, replacement, content)
        if old_content != content:
            changes.append(f"  ✓ Fixed reporter import: from .reporter -> from ..reporters.reporter")

    # Fix review_reporter import
    pattern = r'from \.review_reporter import'
    if re.search(pattern, content):
        replacement = 'from ..reporters.review_reporter import'
        old_content = content
        content = re.sub(pattern, replacement, content)
        if old_content != content:
            changes.append(f"  ✓ Fixed review_reporter import: from .review_reporter -> from ..reporters.review_reporter")

    return content, changes


def fix_llm_client_imports(content: str, file_path: Path) -> Tuple[str, List[str]]:
    """
    Fix LLMClient imports to use the correct module path.

    Changes:
    - from ..llm import LLMClient -> from ..llm.client import LLMClient (in subdirs)
    - from .llm import LLMClient -> from .llm.client import LLMClient (in root level)
    - from ..llm.client -> from .llm.client (in root level files like reviewer.py)
    """
    changes = []

    # Determine if file is at root level (github_feedback/*.py, not github_feedback/subdir/*.py)
    path_str = str(file_path)
    # Extract the part after '/github_feedback/'
    if '/github_feedback/' in path_str:
        after_pkg = path_str.split('/github_feedback/')[-1]
        # If there's no '/' in the part after github_feedback/, it's a root level file
        is_root_level = '/' not in after_pkg
    else:
        is_root_level = False

    # For root level files, fix ..llm.client -> .llm.client
    if is_root_level:
        pattern = r'from \.\.llm\.client import'
        if re.search(pattern, content):
            replacement = 'from .llm.client import'
            old_content = content
            content = re.sub(pattern, replacement, content)
            if old_content != content:
                changes.append(f"  ✓ Fixed LLMClient import: from ..llm.client -> from .llm.client")

        pattern = r'from \.\.llm import'
        if re.search(pattern, content):
            replacement = 'from .llm.client import'
            old_content = content
            content = re.sub(pattern, replacement, content)
            if old_content != content:
                changes.append(f"  ✓ Fixed LLMClient import: from ..llm -> from .llm.client")

    # For subdirectory files
    else:
        pattern = r'from \.\.llm import LLMClient'
        if re.search(pattern, content):
            replacement = 'from ..llm.client import LLMClient'
            old_content = content
            content = re.sub(pattern, replacement, content)
            if old_content != content:
                changes.append(f"  ✓ Fixed LLMClient import: from ..llm -> from ..llm.client")

        pattern = r'from \.llm import LLMClient'
        if re.search(pattern, content):
            # This could be in cli (needs ..) or root (needs .)
            # For cli files, it should be ..llm.client
            if 'github_feedback/cli/' in str(file_path):
                replacement = 'from ..llm.client import LLMClient'
            else:
                replacement = 'from .llm.client import LLMClient'

            old_content = content
            content = re.sub(pattern, replacement, content)
            if old_content != content:
                changes.append(f"  ✓ Fixed LLMClient import: from .llm -> from {replacement.split()[1]}")

    return content, changes


def fix_llm_module_imports(content: str, file_path: Path) -> Tuple[str, List[str]]:
    """
    Fix imports in llm/client.py.

    Changes:
    - from .hybrid_analysis -> from ..hybrid_analysis
    - from .llm_cache -> from .cache
    - from .llm_heuristics -> from .heuristics
    - from .llm_metrics -> from .metrics
    - from .llm_validation -> from .validation
    - from .prompts -> from ..prompts
    """
    changes = []

    # Only fix llm/client.py
    if not str(file_path).endswith('llm/client.py'):
        return content, changes

    # Map of incorrect imports to correct ones
    import_fixes = {
        '.hybrid_analysis': '..hybrid_analysis',
        '.llm_cache': '.cache',
        '.llm_heuristics': '.heuristics',
        '.llm_metrics': '.metrics',
        '.llm_validation': '.validation',
        '.prompts': '..prompts',
    }

    for old_import, new_import in import_fixes.items():
        pattern = rf'from {re.escape(old_import)} import'

        if re.search(pattern, content):
            new_import_statement = f'from {new_import} import'
            old_content = content
            content = re.sub(pattern, new_import_statement, content)

            if old_content != content:
                changes.append(f"  ✓ Fixed import: from {old_import} -> from {new_import}")

    return content, changes


def fix_reporters_imports(content: str, file_path: Path) -> Tuple[str, List[str]]:
    """
    Fix imports in reporters/ directory.

    Changes:
    - from .feedback_builders -> from ..feedback_builders.feedback_builder
    - from .retrospective_builders -> from ..retrospective_builders.retro_builder
    - from .section_builders.* -> from ..section_builders.*
    - from .review_reports -> from ..review_reports (in re-export files)
    - from .year_in_review -> from ..year_in_review (in re-export files)
    """
    changes = []

    # Only fix files in reporters directory
    if 'github_feedback/reporters/' not in str(file_path):
        return content, changes

    # Fix feedback_builders import
    pattern = r'from \.feedback_builders import FeedbackBuilder'
    if re.search(pattern, content):
        replacement = 'from ..feedback_builders.feedback_builder import FeedbackBuilder'
        old_content = content
        content = re.sub(pattern, replacement, content)
        if old_content != content:
            changes.append(f"  ✓ Fixed import: from .feedback_builders -> from ..feedback_builders.feedback_builder")

    # Fix retrospective_builders import
    pattern = r'from \.retrospective_builders import'
    if re.search(pattern, content):
        replacement = 'from ..retrospective_builders.retro_builder import'
        old_content = content
        content = re.sub(pattern, replacement, content)
        if old_content != content:
            changes.append(f"  ✓ Fixed import: from .retrospective_builders -> from ..retrospective_builders.retro_builder")

    # Fix section_builders imports
    pattern = r'from \.section_builders\.'
    if re.search(pattern, content):
        replacement = 'from ..section_builders.'
        old_content = content
        content = re.sub(pattern, replacement, content)
        if old_content != content:
            changes.append(f"  ✓ Fixed imports: from .section_builders.* -> from ..section_builders.*")

    # Fix re-export imports for review_reports
    pattern = r'from \.review_reports import'
    if re.search(pattern, content):
        replacement = 'from ..review_reports import'
        old_content = content
        content = re.sub(pattern, replacement, content)
        if old_content != content:
            changes.append(f"  ✓ Fixed import: from .review_reports -> from ..review_reports")

    # Fix re-export imports for year_in_review
    pattern = r'from \.year_in_review import'
    if re.search(pattern, content):
        replacement = 'from ..year_in_review import'
        old_content = content
        content = re.sub(pattern, replacement, content)
        if old_content != content:
            changes.append(f"  ✓ Fixed import: from .year_in_review -> from ..year_in_review")

    return content, changes


def process_file(file_path: Path) -> None:
    """Process a single Python file to fix imports."""
    try:
        content = read_file(file_path)
        original_content = content
        all_changes = []

        # Apply all fixes
        content, changes = fix_collector_imports(content, file_path)
        all_changes.extend(changes)

        content, changes = fix_core_module_imports(content, file_path)
        all_changes.extend(changes)

        content, changes = fix_single_dot_core_imports(content, file_path)
        all_changes.extend(changes)

        content, changes = fix_collector_module_imports(content, file_path)
        all_changes.extend(changes)

        content, changes = fix_all_collectors_imports(content, file_path)
        all_changes.extend(changes)

        content, changes = fix_cli_analyzer_imports(content, file_path)
        all_changes.extend(changes)

        content, changes = fix_cli_root_module_imports(content, file_path)
        all_changes.extend(changes)

        content, changes = fix_llm_client_imports(content, file_path)
        all_changes.extend(changes)

        content, changes = fix_llm_module_imports(content, file_path)
        all_changes.extend(changes)

        content, changes = fix_reporters_imports(content, file_path)
        all_changes.extend(changes)

        # Only write if changes were made
        if content != original_content:
            write_file(file_path, content)
            rel_path = file_path.relative_to(get_project_root())
            print(f"\n✅ Fixed: {rel_path}")
            for change in all_changes:
                print(change)
            return True

        return False

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False


def main():
    """Main function to fix all imports in the codebase."""
    root = get_project_root()
    github_feedback_dir = root / "github_feedback"

    print("=" * 80)
    print("GitHub Feedback Analysis - Import Fixer")
    print("=" * 80)
    print()
    print("Scanning for Python files with import errors...")
    print()

    # Find all Python files
    python_files = list(github_feedback_dir.rglob("*.py"))
    # Exclude __pycache__ and __init__ files (usually don't need fixing)
    python_files = [
        f for f in python_files
        if '__pycache__' not in str(f)
    ]

    print(f"Found {len(python_files)} Python files to check")
    print()

    # Track fixes
    files_fixed = 0

    # Process each file
    for file_path in sorted(python_files):
        if process_file(file_path):
            files_fixed += 1

    print()
    print("=" * 80)
    print(f"Summary: Fixed {files_fixed} files")
    print("=" * 80)
    print()

    if files_fixed > 0:
        print("✅ Import fixes completed successfully!")
        print()
        print("Next steps:")
        print("  1. Review the changes")
        print("  2. Test the CLI: python -m github_feedback.cli.main --help")
        print("  3. Run tests: pytest")
    else:
        print("ℹ️  No import issues found!")


if __name__ == "__main__":
    main()
