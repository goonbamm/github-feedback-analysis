"""Analysis thresholds and scoring constants."""

from __future__ import annotations

# =============================================================================
# Analysis Thresholds
# =============================================================================

# Activity level thresholds for insights and awards
ACTIVITY_THRESHOLDS = {
    # Commit thresholds
    'very_high_commits': 200,
    'high_commits': 100,
    'moderate_commits': 50,

    # Pull request thresholds
    'very_high_prs': 50,
    'high_prs': 30,
    'moderate_prs': 10,

    # Review thresholds
    'very_high_reviews': 50,
    'high_reviews': 20,
    'moderate_reviews': 10,

    # Issue thresholds
    'moderate_issues': 20,

    # Code change thresholds
    'very_large_pr': 10000,  # Lines changed
    'large_pr': 1000,  # Lines changed

    # Ratio thresholds
    'high_commits_per_pr': 5,
    'high_review_ratio': 2,  # Reviews / PRs
    'high_merge_rate': 0.8,  # 80% merge rate

    # Collaboration thresholds
    'moderate_doc_prs': 3,
    'moderate_test_prs': 5,
    'feature_pr_threshold': 5,
}

# Consistency score interpretation thresholds
CONSISTENCY_THRESHOLDS = {
    'very_consistent': 0.7,  # Above this is very consistent
    'inconsistent': 0.3,  # Below this is inconsistent
}

# Trend analysis thresholds
TREND_THRESHOLDS = {
    'increasing_multiplier': 1.2,  # 20% increase
    'decreasing_multiplier': 0.8,  # 20% decrease
    'minimum_months_for_trend': 3,  # Need at least 3 months for trend analysis
}

# Award calculation thresholds - Consistency awards
AWARD_CONSISTENCY_THRESHOLDS = {
    'consistent_months': 6,  # Minimum months for consistency award
    'consistent_activity_per_month': 20,  # Minimum activity per month
    'sprint_months': 3,  # Minimum months for sprint award
    'sprint_velocity': 30,  # Minimum velocity for sprint award
}

# Award calculation thresholds - Balanced contributor awards
AWARD_BALANCED_THRESHOLDS = {
    'allrounder_commits': 50,  # Minimum commits for all-rounder award
    'allrounder_prs': 15,  # Minimum PRs for all-rounder award
    'allrounder_reviews': 15,  # Minimum reviews for all-rounder award
    'balanced_min_ratio': 0.2,  # Minimum ratio for balanced contribution (20%)
    'balanced_max_ratio': 0.5,  # Maximum ratio for balanced contribution (50%)
    'renaissance_commits': 100,  # Minimum commits for renaissance developer
    'renaissance_prs': 30,  # Minimum PRs for renaissance developer
    'renaissance_reviews': 50,  # Minimum reviews for renaissance developer
    'renaissance_issues': 10,  # Minimum issues for renaissance developer
}

# Award calculation thresholds - PR characteristics
AWARD_PR_THRESHOLDS = {
    'micro_pr_size': 50,  # Maximum lines changed for micro PR
    'micro_pr_count': 10,  # Minimum count of small PRs for micro-commit artist award
}

# =============================================================================
# Retrospective Analysis Thresholds
# =============================================================================

# Change significance thresholds for time comparisons
RETROSPECTIVE_CHANGE_THRESHOLDS = {
    'major_change_pct': 50,  # > 50% change is major
    'moderate_change_pct': 20,  # > 20% change is moderate
    # <= 20% change is minor
}

# Impact assessment thresholds for different contribution types
IMPACT_ASSESSMENT_THRESHOLDS = {
    # Commit impact levels
    'commits_high_impact': 200,  # > 200 commits is high impact
    'commits_medium_impact': 50,  # > 50 commits is medium impact
    # <= 50 commits is low impact

    # PR impact levels
    'prs_high_impact': 50,  # > 50 PRs is high impact
    'prs_medium_impact': 20,  # > 20 PRs is medium impact
    # <= 20 PRs is low impact

    # Review impact levels
    'reviews_high_impact': 100,  # > 100 reviews is high impact
    'reviews_medium_impact': 30,  # > 30 reviews is medium impact
    # <= 30 reviews is low impact
}

# =============================================================================
# Critique/Analysis Thresholds
# =============================================================================

# Thresholds for identifying code quality issues
CRITIQUE_THRESHOLDS = {
    # Commit message quality
    'poor_commit_ratio': 0.25,  # 25% poor messages triggers critique (lowered from 0.4)

    # PR size thresholds
    'large_pr_lines': 500,  # PRs larger than this are considered large (lowered from 1000)
    'large_pr_ratio': 0.2,  # 20% large PRs triggers critique (lowered from 0.3)
    'recommended_pr_size': 300,  # Recommended max PR size

    # PR title quality
    'vague_title_ratio': 0.2,  # 20% vague titles triggers critique (lowered from 0.3)

    # Review quality
    'neutral_review_ratio': 0.4,  # 40% neutral reviews triggers critique (lowered from 0.6)
    'review_pr_ratio': 0.5,  # Reviews should be at least 50% of PRs

    # Activity consistency
    'min_commits_per_month': 5,  # Minimum commits per month for consistency (lowered from 10)

    # Documentation thresholds
    'min_doc_pr_ratio': 0.05,  # At least 5% of PRs should be documentation

    # Test coverage thresholds
    'min_test_pr_ratio': 0.1,  # At least 10% of PRs should include tests

    # Branch management
    'max_commits_per_pr': 15,  # PRs with more than 15 commits may need better branch management

    # Issue tracking
    'min_issue_ratio': 0.1,  # Issues should be at least 10% of total activity

    # Collaboration diversity
    'min_unique_reviewers': 2,  # Should have at least 2 unique reviewers
}

# =============================================================================
# Collaboration & Review Thresholds
# =============================================================================

# Collaboration level thresholds
COLLABORATION_LEVEL_THRESHOLDS = {
    'high_engagement': 50,  # > 50 reviews is high engagement
    'moderate_engagement': 20,  # > 20 reviews is moderate engagement
    'high_collaborators': 10,  # > 10 unique collaborators is high
    'moderate_collaborators': 5,  # > 5 unique collaborators is moderate
    'core_collaborator_reviews': 10,  # > 10 reviews makes someone a core collaborator
}

# Review quality and ratio thresholds
REVIEW_QUALITY_THRESHOLDS = {
    'constructive_ratio': 0.8,  # >= 80% constructive reviews is excellent
    'merge_rate_excellent': 0.9,  # >= 90% merge rate is excellent
    'merge_rate_good': 0.8,  # >= 80% merge rate is good
    'optimal_review_to_pr_ratio': 3.0,  # 3:1 review to PR ratio
    'min_review_to_pr_ratio': 0.5,  # Minimum 50% reviews compared to PRs
}

# =============================================================================
# Activity Consistency Thresholds
# =============================================================================

# Consistency and variance thresholds
CONSISTENCY_VARIANCE_THRESHOLDS = {
    'very_consistent': 0.3,  # < 0.3 normalized variance is very consistent
    'inconsistent': 0.5,  # > 0.5 normalized variance is inconsistent
    'burnout_indicators_warning': 2,  # >= 2 burnout indicators is a warning
    'burnout_indicators_risk': 1,  # 1 burnout indicator is at risk
}

# =============================================================================
# Tech Stack & Expertise Thresholds
# =============================================================================

# Tech stack diversity and expertise thresholds
TECH_STACK_THRESHOLDS = {
    'high_diversity': 0.6,  # > 0.6 diversity score is high
    'expert_ratio': 0.7,  # > 70% usage of primary language is expert
    'proficient_ratio': 0.5,  # > 50% usage of primary language is proficient
}

# =============================================================================
# Award Specific Thresholds
# =============================================================================

# Additional award thresholds not covered in AWARD_*_THRESHOLDS
AWARD_ACHIEVEMENT_THRESHOLDS = {
    'huge_pr_size': 1000,  # > 1000 lines changed is a huge PR
    'huge_pr_count': 3,  # >= 3 huge PRs triggers Big Bang award
    'quick_merge_count': 5,  # >= 5 quick merges triggers Speed Demon award
    'min_prs_for_merge_rate': 20,  # Need at least 20 PRs to calculate merge rate
    'doc_pr_count': 5,  # >= 5 documentation PRs triggers Documentarian award
    'test_pr_count': 5,  # >= 5 test PRs triggers Test Champion award
    'refactor_pr_count': 5,  # >= 5 refactor PRs triggers Refactoring Master award
    'bug_pr_count': 10,  # >= 10 bug fix PRs triggers Bug Squasher award
    'feature_pr_count': 10,  # >= 10 feature PRs triggers Feature Builder award
}
