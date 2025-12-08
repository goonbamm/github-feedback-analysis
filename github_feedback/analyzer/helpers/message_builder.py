"""Helper class for building activity-based messages with threshold checks."""

from __future__ import annotations

from typing import List, Optional


class ActivityMessageBuilder:
    """Helper class for building activity-based messages with threshold checks."""

    @staticmethod
    def build_if_exceeds(
        value: int | float,
        threshold: int | float,
        message_template: str,
        *format_args
    ) -> Optional[str]:
        """Build a message if value exceeds threshold.

        Args:
            value: The value to check
            threshold: The threshold to compare against
            message_template: Template string with placeholders
            *format_args: Arguments to format the template

        Returns:
            Formatted message if value > threshold, None otherwise
        """
        if value > threshold:
            return message_template.format(*format_args)
        return None

    @staticmethod
    def build_messages_from_checks(
        checks: List[tuple[int | float, int | float, str, tuple]]
    ) -> List[str]:
        """Build messages from a list of threshold checks.

        Args:
            checks: List of (value, threshold, template, args) tuples

        Returns:
            List of messages where threshold was exceeded
        """
        messages = []
        for value, threshold, template, args in checks:
            msg = ActivityMessageBuilder.build_if_exceeds(value, threshold, template, *args)
            if msg:
                messages.append(msg)
        return messages
