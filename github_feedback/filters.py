"""Filtering utilities for GitHub data."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Set

from .core.models import AnalysisFilters

# Language extension mapping
LANGUAGE_EXTENSION_MAP: Dict[str, str] = {
    "py": "Python",
    "js": "JavaScript",
    "ts": "TypeScript",
    "tsx": "TypeScript",
    "jsx": "JavaScript",
    "rb": "Ruby",
    "go": "Go",
    "rs": "Rust",
    "java": "Java",
    "cs": "C#",
    "cpp": "C++",
    "cxx": "C++",
    "cc": "C++",
    "c": "C",
    "kt": "Kotlin",
    "swift": "Swift",
    "php": "PHP",
    "scala": "Scala",
    "m": "Objective-C",
    "mm": "Objective-C++",
    "hs": "Haskell",
    "r": "R",
    "pl": "Perl",
    "sh": "Shell",
    "ps1": "PowerShell",
    "dart": "Dart",
    "md": "Markdown",
    "yml": "YAML",
    "yaml": "YAML",
    "json": "JSON",
}


class FilterHelper:
    """Helper class for applying filters to GitHub data."""

    @staticmethod
    def filter_bot(author: Optional[Dict[str, Any]], filters: AnalysisFilters) -> bool:
        """Check if author should be filtered as a bot.

        Args:
            author: GitHub author object
            filters: Analysis filters configuration

        Returns:
            True if author is a bot and should be filtered, False otherwise
        """
        if not filters.exclude_bots:
            return False
        if not author:
            return False
        return author.get("type") == "Bot"

    @staticmethod
    def apply_file_filters(
        filenames: List[str],
        filters: AnalysisFilters,
    ) -> bool:
        """Apply path and language filters to a list of filenames.

        Args:
            filenames: List of file paths to check
            filters: Analysis filters to apply

        Returns:
            True if filenames pass all filters, False otherwise
        """
        if not filters.include_paths and not filters.exclude_paths and not filters.include_languages:
            return True

        # Check include_paths filter
        if filters.include_paths:
            if not any(
                FilterHelper.path_matches(filename, include_path)
                for filename in filenames
                for include_path in filters.include_paths
            ):
                return False

        # Check exclude_paths filter
        if filters.exclude_paths:
            if any(
                FilterHelper.path_matches(filename, exclude_path)
                for filename in filenames
                for exclude_path in filters.exclude_paths
            ):
                return False

        # Check include_languages filter
        if filters.include_languages:
            include_languages_normalised = FilterHelper.normalise_language_filters(
                filters.include_languages
            )
            if include_languages_normalised:
                file_language_tokens = {
                    token
                    for filename in filenames
                    for token in FilterHelper.filename_language_tokens(filename)
                }
                if not file_language_tokens.intersection(include_languages_normalised):
                    return False

        return True

    @staticmethod
    def path_matches(path: str, prefix: str) -> bool:
        """Check if path matches the given prefix.

        Args:
            path: File path to check
            prefix: Path prefix to match against

        Returns:
            True if path matches prefix
        """
        if not prefix:
            return True
        return path.startswith(prefix)

    @staticmethod
    def pr_matches_branch_filters(
        pr: Dict[str, Any], filters: AnalysisFilters
    ) -> bool:
        """Check if PR matches branch filters.

        Args:
            pr: GitHub pull request object
            filters: Analysis filters configuration

        Returns:
            True if PR passes branch filters
        """
        include = filters.include_branches
        exclude = set(filters.exclude_branches)
        base_ref = ((pr.get("base") or {}).get("ref") or "")
        head_ref = ((pr.get("head") or {}).get("ref") or "")

        if base_ref in exclude or head_ref in exclude:
            return False
        if include:
            return base_ref in include or head_ref in include
        return True

    @staticmethod
    def normalise_language_filters(include_languages: Sequence[str]) -> Set[str]:
        """Normalise language filter strings.

        Args:
            include_languages: List of language filters

        Returns:
            Set of normalised language tokens
        """
        normalised: Set[str] = set()
        for value in include_languages:
            token = str(value or "").strip().lower()
            if not token:
                continue
            token = token.lstrip(".")
            if token:
                normalised.add(token)
        return normalised

    @staticmethod
    def filename_language_tokens(filename: str) -> Set[str]:
        """Extract language tokens from filename.

        Args:
            filename: File name to analyze

        Returns:
            Set of language tokens (extension and language name)
        """
        tokens: Set[str] = set()
        if "." not in filename:
            return tokens
        extension = filename.rsplit(".", 1)[-1].lower()
        if not extension:
            return tokens
        tokens.add(extension)
        language = LANGUAGE_EXTENSION_MAP.get(extension)
        if language:
            tokens.add(language.lower())
        return tokens

    @staticmethod
    def filename_to_language(filename: str) -> Optional[str]:
        """Convert filename to language name.

        Args:
            filename: File name to analyze

        Returns:
            Language name or None if not recognized
        """
        if "." not in filename:
            return None
        extension = filename.rsplit(".", 1)[-1].lower()
        if not extension:
            return None
        return LANGUAGE_EXTENSION_MAP.get(extension)

    @staticmethod
    def extract_issue_files(issue: Dict[str, Any]) -> List[str]:
        """Extract file paths from issue metadata.

        Args:
            issue: GitHub issue object

        Returns:
            List of file paths mentioned in issue
        """
        files: List[str] = []
        issue_files = issue.get("files")
        if isinstance(issue_files, list):
            files.extend(str(filename) for filename in issue_files)
        labels = issue.get("labels") or []
        for label in labels:
            name = str((label or {}).get("name") or "")
            if name.startswith("path:"):
                files.append(name.split("path:", 1)[1])
            if name.startswith("file:"):
                files.append(name.split("file:", 1)[1])
        return files
