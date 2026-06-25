import re

# Size limit: 256 KiB (256 * 1024 bytes)
MAX_MARKDOWN_BYTES = 262144

# Regex patterns for validation
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|password|secret|token)\b\s*[:=]\s*['\"]?[A-Za-z0-9_-]{6,}['\"]?"
)
BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_.-]{12,}\b")
SAFETY_ID_PATTERN = re.compile(r"\b(?:RED|SIG)-[0-9]{3}\b")

STACK_TRACE_MARKERS = [
    "Traceback (most recent call last)",
    "ValidationError",
    "Exception:",
    "Stack trace",
]

PROVENANCE_INTERNAL_PATTERNS = [
    re.compile(r"(?i)\bsource_segment_ids\b\s*[:=]"),
    re.compile(r"(?i)\bderived_from_ids\b\s*[:=]"),
    re.compile(r"(?i)\btransformation\b\s*[:=]"),
    re.compile(r"(?i)\brationale\b\s*[:=]"),
]


def validate_markdown_output(markdown: str) -> str:
    """Validates rendered Markdown output before returning it to the caller.

    Raises ValueError if any safety or resource limits are violated.
    Returns the exact, unmodified markdown string if safe.
    """
    if not markdown or not markdown.strip():
        raise ValueError("Markdown output cannot be empty or whitespace-only")

    # 1. Byte length validation (256 KiB limit)
    byte_len = len(markdown.encode("utf-8"))
    if byte_len > MAX_MARKDOWN_BYTES:
        raise ValueError(
            f"Markdown output too large: {byte_len} bytes "
            f"(maximum allowed is {MAX_MARKDOWN_BYTES} bytes)"
        )

    # 2. Raw secret assignment check
    if SECRET_ASSIGNMENT_PATTERN.search(markdown):
        raise ValueError("Markdown output contains raw secret assignments")
    if BEARER_PATTERN.search(markdown):
        raise ValueError("Markdown output contains raw Bearer token pattern")

    # 3. Stack trace and validation exceptions check
    for marker in STACK_TRACE_MARKERS:
        if marker in markdown:
            raise ValueError(f"Markdown output contains error traceback marker: {marker}")

    # 4. Internal safety IDs check
    if SAFETY_ID_PATTERN.search(markdown):
        raise ValueError("Markdown output contains raw safety event IDs")

    # 5. Provenance internals check (key-like pattern search)
    for pattern in PROVENANCE_INTERNAL_PATTERNS:
        if pattern.search(markdown):
            raise ValueError(f"Markdown output contains raw provenance keys matching: {pattern.pattern}")

    return markdown
