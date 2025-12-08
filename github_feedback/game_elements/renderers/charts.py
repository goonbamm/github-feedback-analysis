"""차트 렌더링 메소드."""
from __future__ import annotations

from typing import Any, Dict, List

from ..constants import COLOR_PALETTE


class ChartRenderer:
    """차트 스타일 렌더링 클래스."""

    @staticmethod
    def render_monthly_chart(
        monthly_data: List[Dict[str, Any]],
        title: str = "월별 활동 트렌드",
        value_key: str = "count",
        label_key: str = "month"
    ) -> List[str]:
        """월별 차트 렌더링 (세로 막대 그래프 스타일).

        Args:
            monthly_data: 월별 데이터 리스트 [{"month": "2024-01", "count": 10}, ...]
            title: 차트 제목
            value_key: 값 키 이름
            label_key: 레이블 키 이름

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        if not monthly_data:
            return lines

        # 최대값 찾기
        max_value = max((item.get(value_key, 0) for item in monthly_data), default=1)
        if max_value == 0:
            max_value = 1

        # 차트 컨테이너
        lines.append('<div style="border: 2px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 16px 0; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">')
        lines.append(f'  <h4 style="margin: 0 0 16px 0; color: #2d3748; font-size: 1.2em;">{title}</h4>')

        # 차트 영역
        lines.append('  <div style="display: flex; align-items: flex-end; justify-content: space-around; height: 200px; border-bottom: 2px solid #cbd5e0; padding: 0 8px;">')

        for item in monthly_data:
            label = item.get(label_key, "")
            value = item.get(value_key, 0)
            height_percent = (value / max_value) * 100 if max_value > 0 else 0

            # 막대 및 레이블
            lines.append('    <div style="display: flex; flex-direction: column; align-items: center; flex: 1; margin: 0 4px;">')
            lines.append(f'      <div style="font-size: 0.8em; font-weight: bold; color: #4a5568; margin-bottom: 4px;">{value}</div>')
            lines.append(f'      <div style="width: 100%; max-width: 60px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); border-radius: 4px 4px 0 0; height: {height_percent}%; min-height: 4px;"></div>')
            lines.append(f'      <div style="font-size: 0.75em; color: #718096; margin-top: 8px; transform: rotate(-45deg); white-space: nowrap;">{label}</div>')
            lines.append('    </div>')

        lines.append('  </div>')
        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_line_chart(
        data_points: List[Dict[str, Any]],
        title: str = "추세 분석",
        x_key: str = "label",
        y_key: str = "value",
        color: str = None
    ) -> List[str]:
        """라인 차트 렌더링 (월별 트렌드 등에 사용).

        Args:
            data_points: 데이터 포인트 리스트 [{"label": "Jan", "value": 10}, ...]
            title: 차트 제목
            x_key: X축 데이터 키
            y_key: Y축 데이터 키
            color: 라인 색상 (기본값: primary)

        Returns:
            마크다운 라인 리스트
        """
        if not data_points:
            return []

        lines = []
        line_color = color or COLOR_PALETTE["primary"]

        # 최대값 찾기
        max_value = max((item.get(y_key, 0) for item in data_points), default=1)
        if max_value == 0:
            max_value = 1

        # 차트 컨테이너
        lines.append('<div style="border: 2px solid ' + COLOR_PALETTE["gray_200"] + '; border-radius: 12px; padding: 24px; margin: 16px 0; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">')
        lines.append(f'  <h4 style="margin: 0 0 20px 0; color: {COLOR_PALETTE["gray_800"]}; font-size: 1.3em;">{title}</h4>')

        # SVG 라인 차트
        width = 800
        height = 300
        padding = 40
        chart_width = width - 2 * padding
        chart_height = height - 2 * padding

        lines.append(f'  <svg width="100%" height="{height}" viewBox="0 0 {width} {height}" style="overflow: visible;">')

        # 배경 그리드
        for i in range(5):
            y = padding + (chart_height / 4) * i
            lines.append(f'    <line x1="{padding}" y1="{y}" x2="{width - padding}" y2="{y}" stroke="{COLOR_PALETTE["gray_200"]}" stroke-width="1" stroke-dasharray="5,5"/>')

        # 데이터 포인트 계산
        num_points = len(data_points)
        x_step = chart_width / (num_points - 1) if num_points > 1 else 0

        # 라인 패스 생성
        path_points = []
        for idx, item in enumerate(data_points):
            value = item.get(y_key, 0)
            x = padding + idx * x_step
            y = padding + chart_height - (value / max_value * chart_height)
            path_points.append(f"{x},{y}")

        path_d = "M " + " L ".join(path_points)

        # 그라데이션 영역
        area_points = path_points + [
            f"{width - padding},{padding + chart_height}",
            f"{padding},{padding + chart_height}"
        ]
        area_d = "M " + " L ".join(area_points) + " Z"

        # 그라데이션 정의
        lines.append(f'    <defs>')
        lines.append(f'      <linearGradient id="lineGradient" x1="0%" y1="0%" x2="0%" y2="100%">')
        lines.append(f'        <stop offset="0%" style="stop-color:{line_color};stop-opacity:0.3" />')
        lines.append(f'        <stop offset="100%" style="stop-color:{line_color};stop-opacity:0.05" />')
        lines.append(f'      </linearGradient>')
        lines.append(f'    </defs>')

        # 영역 채우기
        lines.append(f'    <path d="{area_d}" fill="url(#lineGradient)"/>')

        # 라인 그리기
        lines.append(f'    <path d="{path_d}" fill="none" stroke="{line_color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')

        # 데이터 포인트 및 레이블
        for idx, item in enumerate(data_points):
            value = item.get(y_key, 0)
            label = item.get(x_key, "")
            x = padding + idx * x_step
            y = padding + chart_height - (value / max_value * chart_height)

            # 포인트
            lines.append(f'    <circle cx="{x}" cy="{y}" r="5" fill="white" stroke="{line_color}" stroke-width="3"/>')

            # X축 레이블
            lines.append(f'    <text x="{x}" y="{height - 10}" text-anchor="middle" fill="{COLOR_PALETTE["gray_600"]}" font-size="12">{label}</text>')

        lines.append('  </svg>')
        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_donut_chart(
        segments: List[Dict[str, Any]],
        title: str = "분포 현황",
        label_key: str = "label",
        value_key: str = "value",
        color_key: str = "color"
    ) -> List[str]:
        """도넛 차트 렌더링 (비율 데이터 시각화).

        Args:
            segments: 세그먼트 리스트 [{"label": "Python", "value": 45, "color": "#3b82f6"}, ...]
            title: 차트 제목
            label_key: 레이블 키
            value_key: 값 키
            color_key: 색상 키

        Returns:
            마크다운 라인 리스트
        """
        if not segments:
            return []

        lines = []

        # 총합 계산
        total = sum(seg.get(value_key, 0) for seg in segments)
        if total == 0:
            return []

        # 차트 컨테이너
        lines.append('<div style="border: 2px solid ' + COLOR_PALETTE["gray_200"] + '; border-radius: 12px; padding: 24px; margin: 16px 0; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">')
        lines.append(f'  <h4 style="margin: 0 0 20px 0; color: {COLOR_PALETTE["gray_800"]}; font-size: 1.3em;">{title}</h4>')
        lines.append('  <div style="display: flex; align-items: center; justify-content: space-around; flex-wrap: wrap;">')

        # SVG 도넛 차트
        size = 300
        center = size / 2
        radius = 100
        inner_radius = 60

        lines.append(f'    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">')

        # 세그먼트 그리기
        current_angle = -90  # 12시 방향부터 시작

        for seg in segments:
            value = seg.get(value_key, 0)
            percentage = (value / total) * 100
            angle = (value / total) * 360

            # 색상 (기본값 사용)
            seg_color = seg.get(color_key, COLOR_PALETTE["primary"])

            # 시작 각도와 끝 각도 계산 (라디안)
            start_angle_rad = current_angle * 3.14159 / 180
            end_angle_rad = (current_angle + angle) * 3.14159 / 180

            # 호의 좌표 계산
            x1 = center + radius * __import__('math').cos(start_angle_rad)
            y1 = center + radius * __import__('math').sin(start_angle_rad)
            x2 = center + radius * __import__('math').cos(end_angle_rad)
            y2 = center + radius * __import__('math').sin(end_angle_rad)

            x3 = center + inner_radius * __import__('math').cos(end_angle_rad)
            y3 = center + inner_radius * __import__('math').sin(end_angle_rad)
            x4 = center + inner_radius * __import__('math').cos(start_angle_rad)
            y4 = center + inner_radius * __import__('math').sin(start_angle_rad)

            # 큰 호 플래그
            large_arc = 1 if angle > 180 else 0

            # 패스 생성
            path_d = f"M {x1},{y1} A {radius},{radius} 0 {large_arc},1 {x2},{y2} L {x3},{y3} A {inner_radius},{inner_radius} 0 {large_arc},0 {x4},{y4} Z"

            lines.append(f'      <path d="{path_d}" fill="{seg_color}" stroke="white" stroke-width="2" opacity="0.9">')
            lines.append(f'        <title>{seg.get(label_key, "")}: {percentage:.1f}%</title>')
            lines.append(f'      </path>')

            current_angle += angle

        # 중앙 텍스트
        lines.append(f'      <text x="{center}" y="{center - 10}" text-anchor="middle" fill="{COLOR_PALETTE["gray_800"]}" font-size="24" font-weight="bold">{total}</text>')
        lines.append(f'      <text x="{center}" y="{center + 15}" text-anchor="middle" fill="{COLOR_PALETTE["gray_600"]}" font-size="14">Total</text>')

        lines.append('    </svg>')

        # 범례
        lines.append('    <div style="display: flex; flex-direction: column; gap: 12px;">')
        for seg in segments:
            value = seg.get(value_key, 0)
            label = seg.get(label_key, "")
            seg_color = seg.get(color_key, COLOR_PALETTE["primary"])
            percentage = (value / total) * 100

            lines.append('      <div style="display: flex; align-items: center; gap: 12px;">')
            lines.append(f'        <div style="width: 20px; height: 20px; background: {seg_color}; border-radius: 4px;"></div>')
            lines.append(f'        <div style="flex: 1;">')
            lines.append(f'          <div style="font-weight: bold; color: {COLOR_PALETTE["gray_800"]};">{label}</div>')
            lines.append(f'          <div style="color: {COLOR_PALETTE["gray_600"]}; font-size: 0.9em;">{value} ({percentage:.1f}%)</div>')
            lines.append(f'        </div>')
            lines.append('      </div>')

        lines.append('    </div>')
        lines.append('  </div>')
        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_radar_chart(
        stats: Dict[str, int],
        title: str = "능력치 레이더",
        size: int = 400
    ) -> List[str]:
        """레이더 차트 렌더링 (RPG 스타일 스탯 시각화).

        Args:
            stats: 스탯 딕셔너리 {"stat_name": value, ...} (0-100 범위)
            title: 차트 제목
            size: 차트 크기 (픽셀)

        Returns:
            마크다운 라인 리스트
        """
        if not stats:
            return []

        lines = []

        # 스탯 이름 매핑 (영문 -> 한글)
        stat_labels = {
            "code_quality": "코드 품질",
            "collaboration": "협업",
            "problem_solving": "문제해결",
            "productivity": "생산성",
            "consistency": "일관성",
            "growth": "성장"
        }

        # 스탯 색상 매핑
        stat_colors = {
            "code_quality": COLOR_PALETTE["stat_code_quality"],
            "collaboration": COLOR_PALETTE["stat_collaboration"],
            "problem_solving": COLOR_PALETTE["stat_problem_solving"],
            "productivity": COLOR_PALETTE["stat_productivity"],
            "consistency": COLOR_PALETTE["stat_consistency"],
            "growth": COLOR_PALETTE["stat_growth"]
        }

        # 차트 컨테이너
        lines.append('<div style="border: 2px solid ' + COLOR_PALETTE["gray_200"] + '; border-radius: 12px; padding: 24px; margin: 16px 0; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">')
        lines.append(f'  <h4 style="margin: 0 0 20px 0; color: {COLOR_PALETTE["gray_800"]}; font-size: 1.3em;">{title}</h4>')
        lines.append('  <div style="display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 40px;">')

        # SVG 레이더 차트
        center = size / 2
        max_radius = (size / 2) - 80  # 여백 확보

        lines.append(f'    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">')

        # 배경 동심원 (20%, 40%, 60%, 80%, 100%)
        for i in range(5, 0, -1):
            radius = max_radius * (i / 5)
            opacity = 0.1 if i % 2 == 0 else 0.05
            lines.append(f'      <circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="{COLOR_PALETTE["gray_300"]}" stroke-width="1" opacity="{opacity}"/>')
            # 레이블 (20, 40, 60, 80, 100)
            if i > 0:
                label_y = center - radius + 5
                lines.append(f'      <text x="{center + 5}" y="{label_y}" fill="{COLOR_PALETTE["gray_400"]}" font-size="10">{i * 20}</text>')

        # 스탯 축 그리기
        stat_items = list(stats.items())
        num_stats = len(stat_items)
        angle_step = 360 / num_stats

        # 축선 및 레이블
        for i, (stat_key, stat_value) in enumerate(stat_items):
            angle = (angle_step * i - 90) * 3.14159 / 180  # -90도로 12시 방향 시작

            # 축선
            end_x = center + max_radius * __import__('math').cos(angle)
            end_y = center + max_radius * __import__('math').sin(angle)
            lines.append(f'      <line x1="{center}" y1="{center}" x2="{end_x}" y2="{end_y}" stroke="{COLOR_PALETTE["gray_300"]}" stroke-width="1"/>')

            # 레이블 위치 (축선 바깥)
            label_radius = max_radius + 40
            label_x = center + label_radius * __import__('math').cos(angle)
            label_y = center + label_radius * __import__('math').sin(angle)

            # 레이블 정렬 조정
            text_anchor = "middle"
            if label_x < center - 5:
                text_anchor = "end"
            elif label_x > center + 5:
                text_anchor = "start"

            stat_label = stat_labels.get(stat_key, stat_key)
            stat_color = stat_colors.get(stat_key, COLOR_PALETTE["primary"])

            lines.append(f'      <text x="{label_x}" y="{label_y}" text-anchor="{text_anchor}" fill="{stat_color}" font-size="14" font-weight="600">{stat_label}</text>')
            lines.append(f'      <text x="{label_x}" y="{label_y + 14}" text-anchor="{text_anchor}" fill="{COLOR_PALETTE["gray_600"]}" font-size="11">({stat_value})</text>')

        # 스탯 폴리곤 (실제 값)
        polygon_points = []
        for i, (stat_key, stat_value) in enumerate(stat_items):
            angle = (angle_step * i - 90) * 3.14159 / 180
            # 값을 0-100 범위로 정규화하여 반지름 계산
            normalized_value = min(100, max(0, stat_value))
            radius = max_radius * (normalized_value / 100)
            point_x = center + radius * __import__('math').cos(angle)
            point_y = center + radius * __import__('math').sin(angle)
            polygon_points.append(f"{point_x},{point_y}")

        # 폴리곤 그리기
        polygon_str = " ".join(polygon_points)
        lines.append(f'      <polygon points="{polygon_str}" fill="{COLOR_PALETTE["primary"]}" fill-opacity="0.3" stroke="{COLOR_PALETTE["primary"]}" stroke-width="2"/>')

        # 스탯 포인트 표시
        for i, (stat_key, stat_value) in enumerate(stat_items):
            angle = (angle_step * i - 90) * 3.14159 / 180
            normalized_value = min(100, max(0, stat_value))
            radius = max_radius * (normalized_value / 100)
            point_x = center + radius * __import__('math').cos(angle)
            point_y = center + radius * __import__('math').sin(angle)

            stat_color = stat_colors.get(stat_key, COLOR_PALETTE["primary"])
            lines.append(f'      <circle cx="{point_x}" cy="{point_y}" r="5" fill="{stat_color}" stroke="white" stroke-width="2"/>')

        lines.append('    </svg>')

        lines.append('  </div>')
        lines.append('</div>')
        lines.append("")

        return lines


__all__ = ["ChartRenderer"]
