"""Tests for SkillTreeBuilder."""

import pytest
from github_feedback.section_builders.skill_tree_builder import SkillTreeBuilder
from github_feedback.models import (
    MetricSnapshot,
    DetailedFeedbackSnapshot,
    CommitFeedback,
    PRTitleFeedback,
    ReviewToneFeedback,
    IssueFeedback,
)


class TestSkillTreeBuilder:
    """Test suite for SkillTreeBuilder refactored methods."""

    @pytest.fixture
    def basic_metrics(self):
        """Create basic metrics for testing."""
        return MetricSnapshot(
            repository="test/repo",
            period="2024-01-01 to 2024-12-31",
            commits=100,
            pull_requests=20,
            reviews=15,
            issues=10,
            months=12,
            velocity_score=8.33,
            awards=["🏆 코드 장인 - 100개 이상의 커밋"],
            highlights=["월평균 8.3회의 활발한 개발 활동"],
        )

    @pytest.fixture
    def detailed_feedback(self):
        """Create detailed feedback for testing."""
        return DetailedFeedbackSnapshot(
            commit_feedback=CommitFeedback(
                total_commits=50,
                good_messages=40,
                poor_messages=10,
                clear_messages=0,  # Not used in current logic
            ),
            pr_title_feedback=PRTitleFeedback(
                total_prs=20,
                clear_titles=16,
                vague_titles=4,
            ),
            review_tone_feedback=ReviewToneFeedback(
                total_reviews=15,
                constructive_reviews=12,
                harsh_reviews=2,
                neutral_reviews=1,
            ),
            issue_feedback=IssueFeedback(
                total_issues=10,
                well_described=8,
                poorly_described=2,
            ),
        )

    def test_extract_skill_name_from_text(self, basic_metrics):
        """Test skill name extraction from award text."""
        builder = SkillTreeBuilder(basic_metrics)

        # Test with emoji and description
        result = builder._extract_skill_name_from_text("🏆 코드 장인 - 100개 이상의 커밋")
        assert result == "코드 장인"

        # Test with emoji only
        result = builder._extract_skill_name_from_text("🏆 코드 장인")
        assert result == "코드 장인"

        # Test with long text (should be truncated)
        long_text = "🏆 " + "A" * 100 + " - description"
        result = builder._extract_skill_name_from_text(long_text)
        assert len(result) <= 50  # Default max length

    def test_collect_acquired_skills_from_awards(self, basic_metrics):
        """Test collecting skills from awards."""
        builder = SkillTreeBuilder(basic_metrics)
        skills = builder._collect_acquired_skills()

        assert len(skills) > 0
        assert skills[0]["type"] == "패시브"
        assert skills[0]["emoji"] == "🏆"
        assert "name" in skills[0]
        assert "mastery" in skills[0]

    def test_collect_acquired_skills_from_highlights(self):
        """Test collecting skills from highlights."""
        metrics = MetricSnapshot(
            repository="test/repo",
            period="2024",
            commits=100,
            pull_requests=20,
            reviews=15,
            issues=10,
            months=12,
            velocity_score=8.33,
            awards=[],  # No awards
            highlights=["월평균 8.3회의 활발한 개발 활동", "팀 협업에 적극 참여"],
        )
        builder = SkillTreeBuilder(metrics)
        skills = builder._collect_acquired_skills()

        assert len(skills) > 0
        # Should have skills from highlights
        assert any(skill["type"] == "액티브" for skill in skills)

    def test_create_commit_skill_with_data(self, basic_metrics, detailed_feedback):
        """Test creating commit skill with valid data."""
        basic_metrics.detailed_feedback = detailed_feedback
        builder = SkillTreeBuilder(basic_metrics)

        skill = builder._create_commit_skill()

        assert skill is not None
        assert skill["emoji"] == "📜"
        assert skill["mastery"] > 0
        assert "커밋" in skill["name"]

    def test_create_commit_skill_without_data(self, basic_metrics):
        """Test creating commit skill returns None without data."""
        builder = SkillTreeBuilder(basic_metrics)
        skill = builder._create_commit_skill()
        assert skill is None

    def test_create_pr_title_skill(self, basic_metrics, detailed_feedback):
        """Test creating PR title skill."""
        basic_metrics.detailed_feedback = detailed_feedback
        builder = SkillTreeBuilder(basic_metrics)

        skill = builder._create_pr_title_skill()

        assert skill is not None
        assert skill["emoji"] == "🎯"
        assert skill["mastery"] == 80  # 16/20 = 80%
        assert "PR" in skill["name"]

    def test_create_review_tone_skill(self, basic_metrics, detailed_feedback):
        """Test creating review tone skill."""
        basic_metrics.detailed_feedback = detailed_feedback
        builder = SkillTreeBuilder(basic_metrics)

        skill = builder._create_review_tone_skill()

        assert skill is not None
        assert skill["emoji"] == "💬"
        assert skill["mastery"] == 80  # 12/15 = 80%
        assert "리뷰" in skill["name"]

    def test_create_issue_skill(self, basic_metrics, detailed_feedback):
        """Test creating issue skill."""
        basic_metrics.detailed_feedback = detailed_feedback
        builder = SkillTreeBuilder(basic_metrics)

        skill = builder._create_issue_skill()

        assert skill is not None
        assert skill["emoji"] == "📋"
        assert skill["mastery"] == 80  # 8/10 = 80%
        assert "이슈" in skill["name"]

    def test_collect_communication_skills(self, basic_metrics, detailed_feedback):
        """Test collecting all communication skills."""
        basic_metrics.detailed_feedback = detailed_feedback
        builder = SkillTreeBuilder(basic_metrics)

        skills = builder._collect_communication_skills()

        # Should have 4 communication skills (commit, PR, review, issue)
        assert len(skills) == 4
        assert all("name" in skill for skill in skills)
        assert all("mastery" in skill for skill in skills)
        assert all("effect" in skill for skill in skills)

    def test_collect_available_skills(self, basic_metrics, detailed_feedback):
        """Test collecting available (not yet acquired) skills."""
        # Add suggestions to feedback
        detailed_feedback.commit_feedback.suggestions = [
            "커밋 메시지에 더 많은 컨텍스트 추가",
            "Why를 명확히 설명"
        ]
        basic_metrics.detailed_feedback = detailed_feedback
        builder = SkillTreeBuilder(basic_metrics)

        skills = builder._collect_available_skills()

        assert len(skills) > 0
        assert all(skill["type"] == "미습득" for skill in skills)
        assert all(skill["mastery"] == 40 for skill in skills)

    def test_build_complete_section(self, basic_metrics, detailed_feedback):
        """Test building complete skill tree section."""
        basic_metrics.detailed_feedback = detailed_feedback
        builder = SkillTreeBuilder(basic_metrics)

        lines = builder.build()

        # Check that section is generated
        assert len(lines) > 0
        assert any("스킬 트리" in line for line in lines)

        # Check structure
        markdown_text = "\n".join(lines)
        assert "##" in markdown_text  # Has heading

    def test_skill_quality_thresholds(self, basic_metrics):
        """Test that skills are categorized correctly based on quality."""
        # Excellent quality (>80%)
        excellent_feedback = DetailedFeedbackSnapshot(
            commit_feedback=CommitFeedback(
                total_commits=100,
                good_messages=85,
                poor_messages=15,
                clear_messages=0,
            ),
        )
        basic_metrics.detailed_feedback = excellent_feedback
        builder = SkillTreeBuilder(basic_metrics)
        skill = builder._create_commit_skill()
        assert skill["type"] == "전설"

        # Good quality (60-80%)
        good_feedback = DetailedFeedbackSnapshot(
            commit_feedback=CommitFeedback(
                total_commits=100,
                good_messages=70,
                poor_messages=30,
                clear_messages=0,
            ),
        )
        basic_metrics.detailed_feedback = good_feedback
        builder = SkillTreeBuilder(basic_metrics)
        skill = builder._create_commit_skill()
        assert skill["type"] == "숙련"

        # Low quality (<60%)
        low_feedback = DetailedFeedbackSnapshot(
            commit_feedback=CommitFeedback(
                total_commits=100,
                good_messages=40,
                poor_messages=60,
                clear_messages=0,
            ),
        )
        basic_metrics.detailed_feedback = low_feedback
        builder = SkillTreeBuilder(basic_metrics)
        skill = builder._create_commit_skill()
        assert skill["type"] == "수련중"
