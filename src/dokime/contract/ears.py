"""The EARS syntax of the text of a requirement."""

import re

_SHALL = re.compile(r"\bshall\b")
_TEMPLATES = (
    re.compile(r"(?!When |While |If |Where )[^,]+ shall \S.*\."),  # ubiquitous
    re.compile(r"When .+, .+ shall \S.*\."),  # event-driven
    re.compile(r"While .+, (?:when .+, )?.+ shall \S.*\."),  # state-driven
    re.compile(r"If .+, then .+ shall \S.*\."),  # unwanted behaviour
    re.compile(r"Where .+, .+ shall \S.*\."),  # optional feature
)


def problem(text: str) -> str | None:
    """Say why a text is not an EARS requirement, or nothing when it is one."""
    if len(_SHALL.findall(text)) > 1:
        return "it has the word 'shall' more than once; write one requirement for each response"
    if not any(template.fullmatch(text) for template in _TEMPLATES):
        return "it matches none of the five EARS templates"
    return None
