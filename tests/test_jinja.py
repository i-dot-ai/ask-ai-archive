from ask_ai.jinja2 import convert_markdown


def test_convert_markdown_sanitises_html():
    dodgy_html = '<script>alert("Oops! This is a malicious script.");</script>'
    converted_markdown = convert_markdown(dodgy_html, False)
    assert "<script>" not in converted_markdown, converted_markdown


def test_convert_markdown_remove_p_tags():
    markdown_text = "**I am bold**"
    expected = "<strong>I am bold</strong>"
    actual = convert_markdown(markdown_text, True)
    assert actual == expected, actual


def test_convert_markdown():
    markdown_text = "**I am bold**"
    expected = "<p><strong>I am bold</strong></p>"
    actual = convert_markdown(markdown_text, False)
    assert actual == expected, actual
