from github_feedback.game_elements import GameRenderer


def test_render_html_table_allows_trusted_markup():
    headers = ["Label", "Count"]
    rows = [["<strong>성장</strong>", "<span style='color: red;'>5</span>"]]

    html_lines = GameRenderer.render_html_table(headers=headers, rows=rows, escape_cells=False)
    html_output = "\n".join(html_lines)

    assert "<strong>성장</strong>" in html_output
    assert "<span style='color: red;'>5</span>" in html_output


def test_render_html_table_escapes_markup_by_default():
    headers = ["Value"]
    rows = [["<em>text</em>"]]

    html_lines = GameRenderer.render_html_table(headers=headers, rows=rows)
    html_output = "\n".join(html_lines)

    assert "&lt;em&gt;text&lt;/em&gt;" in html_output
