import jinja2
from django.templatetags.static import static
from django.urls import reverse
from django.utils.text import slugify
from markdown_it import MarkdownIt

# `js-default` setting required to sanitize inputs
# https://markdown-it-py.readthedocs.io/en/latest/security.html
markdown_converter = MarkdownIt("js-default")


def is_checked(data, name):
    if data.get(name):
        return "checked"
    else:
        return ""


def convert_markdown(text: str, remove_p_tags: bool) -> str:
    html = markdown_converter.render(text).strip()
    if remove_p_tags:
        # Remove <p> tags so don't start on newline
        html = html.removeprefix("<p>")
        html = html.removesuffix("</p>")
    return html


def environment(**options):
    extra_options = dict()
    env = jinja2.Environment(  # nosec B701 (autoescape is set to true)
        **{
            "autoescape": True,
            **options,
            **extra_options,
        }
    )
    env.globals.update(
        {
            "static": static,
            "url": reverse,
            "slugify": slugify,
            "is_checked": is_checked,
            "convert_markdown": convert_markdown,
        }
    )
    return env
