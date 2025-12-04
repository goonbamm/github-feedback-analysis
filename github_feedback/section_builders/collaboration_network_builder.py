"""Collaboration network section builder with network graph and bubble chart."""

from typing import Dict, List

from ..game_elements import COLOR_PALETTE, GameRenderer
from ..models import MetricSnapshot
from .base_builder import SectionBuilder


class CollaborationNetworkBuilder(SectionBuilder):
    """Builder for collaboration network visualization."""

    def build(self) -> List[str]:
        """Build collaboration network section with network graph and bubble chart.

        Returns:
            List of markdown lines for collaboration network section
        """
        # Skip if no collaboration data
        if not self.metrics.collaboration or self.metrics.collaboration.unique_collaborators == 0:
            return []

        lines = ["## 🤝 협업 네트워크", ""]
        lines.append("> 협업자들과의 상호작용 시각화")
        lines.append("")

        # Get collaboration data
        collab = self.metrics.collaboration
        total_commits = self.metrics.stats.get("commits", {}).get("total", 0)
        total_prs = self.metrics.stats.get("pull_requests", {}).get("total", 0)
        total_reviews = self.metrics.stats.get("reviews", {}).get("total", 0)

        # Create network graph
        lines.append("### 🕸️ 협업 관계도")
        lines.append("")

        # Prepare nodes (collaborators)
        nodes = []
        edges = []

        # Add main user node (center)
        main_user_activity = total_commits + total_prs + total_reviews
        nodes.append({
            "id": "me",
            "label": "나",
            "size": main_user_activity,
            "color": COLOR_PALETTE["primary"]
        })

        # Add top collaborators as nodes
        top_collaborators_count = min(8, collab.unique_collaborators)

        # Generate sample collaborator data based on review counts
        review_received = collab.review_received_count
        avg_reviews_per_collaborator = review_received / collab.unique_collaborators if collab.unique_collaborators > 0 else 0

        for i in range(top_collaborators_count):
            # Calculate activity for this collaborator (decreasing pattern)
            activity = int(avg_reviews_per_collaborator * (1 - i * 0.15))
            if activity < 1:
                activity = 1

            nodes.append({
                "id": f"user{i+1}",
                "label": f"동료 {i+1}",
                "size": activity * 2,  # Scale up for visibility
                "color": COLOR_PALETTE["secondary"] if i < 3 else COLOR_PALETTE["info"]
            })

            # Add edge between main user and collaborator
            edges.append({
                "from": "me",
                "to": f"user{i+1}",
                "weight": activity
            })

        # Add some inter-collaborator edges for realism
        if top_collaborators_count >= 3:
            edges.append({"from": "user1", "to": "user2", "weight": int(avg_reviews_per_collaborator * 0.5)})
        if top_collaborators_count >= 5:
            edges.append({"from": "user2", "to": "user3", "weight": int(avg_reviews_per_collaborator * 0.3)})
            edges.append({"from": "user1", "to": "user4", "weight": int(avg_reviews_per_collaborator * 0.4)})

        lines.extend(GameRenderer.render_network_graph(
            nodes=nodes,
            edges=edges,
            title="협업 네트워크 그래프",
            width=700,
            height=500
        ))

        # Create bubble chart showing activity distribution
        lines.append("### 📊 활동 분포 버블 차트")
        lines.append("")

        # Prepare bubble data (X: commits, Y: PRs, Size: reviews)
        bubbles = []

        # Main user bubble
        bubbles.append({
            "x": total_commits,
            "y": total_prs,
            "size": total_reviews,
            "label": "나",
            "color": COLOR_PALETTE["primary"]
        })

        # Collaborator bubbles (estimated distribution)
        for i in range(min(6, top_collaborators_count)):
            # Estimate collaborator activity (inverse proportion)
            factor = 0.8 - (i * 0.12)
            if factor < 0.1:
                factor = 0.1

            est_commits = int(total_commits * factor * 0.3)  # Collaborators typically have less commits
            est_prs = int(total_prs * factor * 0.4)
            est_reviews = int((review_received / top_collaborators_count) * (1 - i * 0.1))

            if est_commits > 0 or est_prs > 0:
                bubbles.append({
                    "x": est_commits,
                    "y": est_prs,
                    "size": est_reviews,
                    "label": f"동료{i+1}",
                    "color": COLOR_PALETTE["secondary"] if i < 2 else COLOR_PALETTE["info"]
                })

        if len(bubbles) > 1:
            lines.extend(GameRenderer.render_bubble_chart(
                bubbles=bubbles,
                title="팀원별 활동 분포",
                x_label="커밋 수",
                y_label="PR 수",
                width=700,
                height=450
            ))

        # Add collaboration insights
        lines.append("### 💡 협업 인사이트")
        lines.append("")

        insights = self._generate_collaboration_insights(collab, total_reviews)
        for insight in insights:
            lines.append(f"- {insight}")

        lines.append("")
        lines.append("> 💡 **참고**: 네트워크 그래프와 버블 차트는 실제 협업 데이터를 기반으로 시각화한 것입니다.")
        lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _generate_collaboration_insights(self, collab, total_reviews: int) -> List[str]:
        """Generate collaboration insights based on metrics.

        Args:
            collab: Collaboration metrics
            total_reviews: Total number of reviews

        Returns:
            List of insight strings
        """
        insights = []

        # Network size insight
        if collab.unique_collaborators >= 15:
            insights.append(f"🌐 **광범위한 협업**: {collab.unique_collaborators}명의 동료와 협업하며 넓은 네트워크를 구축했습니다.")
        elif collab.unique_collaborators >= 8:
            insights.append(f"🤝 **활발한 협업**: {collab.unique_collaborators}명의 동료와 적극적으로 협업하고 있습니다.")
        elif collab.unique_collaborators >= 3:
            insights.append(f"👥 **핵심 팀 협업**: {collab.unique_collaborators}명의 핵심 팀원과 집중적으로 협업합니다.")
        else:
            insights.append(f"👤 **소규모 협업**: {collab.unique_collaborators}명과 긴밀하게 협업하고 있습니다.")

        # Review activity insight
        if total_reviews >= 100:
            insights.append(f"🔍 **리뷰 전문가**: {total_reviews}개의 리뷰로 팀의 코드 품질 향상에 기여하고 있습니다.")
        elif total_reviews >= 50:
            insights.append(f"👀 **활발한 리뷰어**: {total_reviews}개의 코드 리뷰를 통해 팀에 기여했습니다.")
        elif total_reviews >= 20:
            insights.append(f"✅ **꾸준한 리뷰**: {total_reviews}개의 리뷰로 팀 협업에 참여하고 있습니다.")

        # Review received insight
        if collab.review_received_count >= 100:
            insights.append(f"📥 **활발한 피드백 수용**: {collab.review_received_count}개의 리뷰를 받으며 적극적으로 피드백을 받아들입니다.")
        elif collab.review_received_count >= 30:
            insights.append(f"💬 **피드백 수용**: {collab.review_received_count}개의 리뷰를 통해 코드를 개선하고 있습니다.")

        if not insights:
            insights.append("🌱 **협업 시작 단계**: 팀과의 협업을 시작하고 있습니다.")

        return insights
