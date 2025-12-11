"""Fun statistics analyzer for entertaining insights."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set

from github_feedback.core.models import (
    CollectionResult,
    FileActivity,
    FunStatistics,
    WorkHourDistribution,
)


class FunStatisticsAnalyzer:
    """Analyzer for fun and engaging statistics."""

    # Common commit message keywords to extract
    INTERESTING_KEYWORDS = {
        'fix', 'bug', 'feature', 'add', 'update', 'refactor', 'remove', 'delete',
        'improve', 'optimize', 'clean', 'test', 'docs', 'merge', 'hotfix',
        '수정', '추가', '개선', '삭제', '버그', '기능', '테스트', '문서'
    }

    @staticmethod
    def analyze(
        collection: CollectionResult,
        commit_messages: Optional[List[Dict[str, str]]] = None,
        commit_timestamps: Optional[List[datetime]] = None,
        file_changes: Optional[Dict[str, Dict[str, int]]] = None,
    ) -> FunStatistics:
        """Analyze fun statistics from collection data.

        Args:
            collection: Collection result with PR and commit data
            commit_messages: Optional list of commit message dicts
            commit_timestamps: Optional list of commit timestamps
            file_changes: Optional dict mapping filepath to {additions, deletions, modifications}

        Returns:
            FunStatistics with entertaining insights
        """
        # Analyze work hours if timestamps available
        work_hours = None
        if commit_timestamps:
            work_hours = FunStatisticsAnalyzer._analyze_work_hours(commit_timestamps)

        # Extract commit keywords
        commit_keywords = FunStatisticsAnalyzer._extract_commit_keywords(commit_messages or [])

        # Analyze top modified files
        top_modified_files = FunStatisticsAnalyzer._analyze_file_activity(file_changes or {})

        # Calculate weekend warrior score (placeholder - needs timestamp data)
        weekend_warrior_score = 0.0  # TODO: Calculate from actual timestamp data

        # Calculate average PR size
        avg_pr_size = FunStatisticsAnalyzer._calculate_avg_pr_size(collection)

        # Generate fun facts
        fun_facts = FunStatisticsAnalyzer._generate_fun_facts(
            collection, commit_keywords, work_hours, avg_pr_size
        )

        return FunStatistics(
            work_hours=work_hours,
            commit_keywords=commit_keywords,
            top_modified_files=top_modified_files,
            weekend_warrior_score=weekend_warrior_score,
            avg_pr_size=avg_pr_size,
            fun_facts=fun_facts,
        )

    @staticmethod
    def _analyze_work_hours(timestamps: List[datetime]) -> WorkHourDistribution:
        """Analyze work hour distribution from commit timestamps.

        Args:
            timestamps: List of commit datetime objects

        Returns:
            WorkHourDistribution with hour analysis
        """
        hour_distribution: Dict[int, int] = defaultdict(int)

        for ts in timestamps:
            hour = ts.hour
            hour_distribution[hour] += 1

        # Find peak hours (hours with most activity)
        if hour_distribution:
            sorted_hours = sorted(hour_distribution.items(), key=lambda x: x[1], reverse=True)
            peak_hours = [hour for hour, _ in sorted_hours[:3]]
        else:
            peak_hours = []

        # Determine work style based on peak hours
        work_style = FunStatisticsAnalyzer._determine_work_style(hour_distribution, peak_hours)

        return WorkHourDistribution(
            hour_distribution=dict(hour_distribution),
            peak_hours=peak_hours,
            work_style=work_style,
        )

    @staticmethod
    def _determine_work_style(hour_dist: Dict[int, int], peak_hours: List[int]) -> str:
        """Determine work style based on hour distribution.

        Args:
            hour_dist: Hour distribution dictionary
            peak_hours: List of peak hours

        Returns:
            Work style description
        """
        if not hour_dist:
            return "알 수 없음"

        total_commits = sum(hour_dist.values())

        # Early bird: 5-9am
        early_commits = sum(hour_dist.get(h, 0) for h in range(5, 10))
        early_ratio = early_commits / total_commits if total_commits > 0 else 0

        # Night owl: 10pm-3am
        night_commits = sum(hour_dist.get(h, 0) for h in list(range(22, 24)) + list(range(0, 4)))
        night_ratio = night_commits / total_commits if total_commits > 0 else 0

        # Afternoon: 1-5pm
        afternoon_commits = sum(hour_dist.get(h, 0) for h in range(13, 18))
        afternoon_ratio = afternoon_commits / total_commits if total_commits > 0 else 0

        if night_ratio >= 0.35:
            return "🦉 나이트 아울 (심야 코더)"
        elif early_ratio >= 0.35:
            return "🌅 얼리버드 (아침형 인간)"
        elif afternoon_ratio >= 0.4:
            return "☀️ 오후 활동가"
        else:
            return "⚖️ 균형잡힌 스케줄"

    @staticmethod
    def _extract_commit_keywords(commit_messages: List[Dict[str, str]]) -> Dict[str, int]:
        """Extract and count interesting keywords from commit messages.

        Args:
            commit_messages: List of commit message dictionaries

        Returns:
            Dictionary mapping keywords to their frequency
        """
        keyword_counter = Counter()

        for msg_dict in commit_messages:
            message = msg_dict.get('message', '').lower()
            # Extract words
            words = re.findall(r'\b\w+\b', message)

            for word in words:
                if word in FunStatisticsAnalyzer.INTERESTING_KEYWORDS:
                    keyword_counter[word] += 1

        # Return top 15 keywords
        return dict(keyword_counter.most_common(15))

    @staticmethod
    def _analyze_file_activity(file_changes: Dict[str, Dict[str, int]]) -> List[FileActivity]:
        """Analyze frequently modified files.

        Args:
            file_changes: Dict mapping filepath to change statistics

        Returns:
            List of FileActivity objects for top 10 files
        """
        file_activities = []

        for filepath, stats in file_changes.items():
            file_activities.append(FileActivity(
                filepath=filepath,
                modifications=stats.get('modifications', 0),
                lines_added=stats.get('additions', 0),
                lines_deleted=stats.get('deletions', 0),
            ))

        # Sort by modifications and return top 10
        file_activities.sort(key=lambda x: x.modifications, reverse=True)
        return file_activities[:10]

    @staticmethod
    def _calculate_avg_pr_size(collection: CollectionResult) -> str:
        """Calculate average PR size category.

        Args:
            collection: Collection result

        Returns:
            Size category: "XS", "Small", "Medium", "Large", "XL"
        """
        if not collection.pull_request_examples:
            return "N/A"

        total_changes = sum(
            pr.additions + pr.deletions
            for pr in collection.pull_request_examples
        )
        avg_changes = total_changes / len(collection.pull_request_examples)

        if avg_changes < 10:
            return "XS (초소형)"
        elif avg_changes < 50:
            return "Small (소형)"
        elif avg_changes < 200:
            return "Medium (중형)"
        elif avg_changes < 500:
            return "Large (대형)"
        else:
            return "XL (초대형)"

    @staticmethod
    def _generate_fun_facts(
        collection: CollectionResult,
        keywords: Dict[str, int],
        work_hours: Optional[WorkHourDistribution],
        avg_pr_size: str,
    ) -> List[str]:
        """Generate fun facts about the developer's activity.

        Args:
            collection: Collection result
            keywords: Commit keyword frequencies
            work_hours: Work hour distribution
            avg_pr_size: Average PR size category

        Returns:
            List of fun fact strings
        """
        facts = []

        # Total activity fact
        total_activity = collection.commits + collection.pull_requests + collection.reviews
        facts.append(f"🎯 총 {total_activity:,}번의 활동으로 GitHub를 빛냈습니다!")

        # Code change volume
        if collection.pull_request_examples:
            total_additions = sum(pr.additions for pr in collection.pull_request_examples)
            total_deletions = sum(pr.deletions for pr in collection.pull_request_examples)
            facts.append(f"📝 {total_additions:,}줄을 추가하고 {total_deletions:,}줄을 삭제했습니다!")

            # Refactoring insight
            if total_deletions > total_additions:
                ratio = (total_deletions / total_additions - 1) * 100
                facts.append(f"♻️ 코드 정리의 달인! 추가보다 {ratio:.0f}% 더 많이 삭제했습니다!")

        # Keyword insights
        if keywords:
            top_keyword = max(keywords.items(), key=lambda x: x[1])
            facts.append(f"💬 가장 자주 사용한 커밋 키워드: '{top_keyword[0]}' ({top_keyword[1]}회)")

        # PR size personality
        if avg_pr_size != "N/A":
            facts.append(f"📦 평균 PR 크기: {avg_pr_size}")

        # Work style fact
        if work_hours and work_hours.work_style:
            facts.append(f"⏰ 작업 스타일: {work_hours.work_style}")

        # Collaboration ratio
        if collection.commits > 0:
            collab_ratio = (collection.pull_requests + collection.reviews) / collection.commits
            if collab_ratio > 1:
                facts.append(f"🤝 커밋보다 {collab_ratio:.1f}배 많은 협업 활동!")
            elif collab_ratio > 0.5:
                facts.append(f"🤝 균형잡힌 개인 작업과 협업 비율!")

        # Review dedication
        if collection.pull_requests > 0 and collection.reviews > 0:
            review_ratio = collection.reviews / collection.pull_requests
            if review_ratio >= 2:
                facts.append(f"👀 자신의 PR보다 {review_ratio:.1f}배 많은 리뷰를 남겼습니다!")

        return facts
