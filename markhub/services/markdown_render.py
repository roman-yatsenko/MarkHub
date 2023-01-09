from typing import Tuple

from markdown import Markdown

from markhub.settings import (MARTOR_MARKDOWN_EXTENSION_CONFIGS,
                              MARTOR_MARKDOWN_EXTENSIONS)


def _markdown() -> Markdown:
    """
    Rerurn the Markdown object with martor settings

    Returns:
        Markdown object
    """
    return Markdown(
        extensions=MARTOR_MARKDOWN_EXTENSIONS,
        extension_configs=MARTOR_MARKDOWN_EXTENSION_CONFIGS,
        output_format="html5",
    )

def markdownify(content: str) -> Tuple[str, str]:
    """Convert content to markdown with toc

    Args:
        content (str): _content to convert_
    
    Returns:
        Tuple rendered content and toc:
    """
    markdown = _markdown()
    return markdown.convert(content), markdown.toc
