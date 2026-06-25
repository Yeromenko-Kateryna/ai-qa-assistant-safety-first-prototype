import re
from app.domain_models import (
    SafetyEvent,
    SafetyEventKind,
    SafetyFlag,
    SanitizedInputEnvelope,
    SanitizedSegment,
)

# Simplified, full-expression patterns that are easy to test
SECRET_PATTERNS = [
    re.compile(
        r"(?i)\b(api[_-]?key|password|secret|token)\b\s*[:=]\s*['\"]?[A-Za-z0-9_-]{12,}['\"]?"
    ),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_.-]{24,}\b"),
]

URL_PATTERN = re.compile(r"https?://[^\s]+|www\.[^\s]+")

INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore\s+(all\s+)?previous\s+instructions"),
    re.compile(r"(?i)system\s+prompt"),
    re.compile(r"(?i)you\s+must\s+now\s+act\s+as"),
]

UNSAFE_ACTION_PATTERNS = [
    re.compile(r"(?i)execute\s+(shell\s+)?command"),
    re.compile(r"(?i)run\s+cmd"),
    re.compile(r"(?i)delete\s+files"),
    re.compile(r"(?i)send\s+http\s+request"),
]


def sanitize_requirement_text(raw_text: str) -> SanitizedInputEnvelope:
    if not raw_text or not raw_text.strip():
        raise ValueError("Input text cannot be empty or whitespace-only")

    # Overall length check prior to processing (future pipeline limit)
    if len(raw_text) > 12000:
        raise ValueError("Input text exceeds maximum length of 12,000 characters")

    segment_id = "SEG-001"
    safety_flags = []
    safety_event_ids = []
    safety_events = []

    red_counter = 1
    sig_counter = 1

    sanitized_text = raw_text

    # 1. Redact Secrets using re.sub with a callback replacing the entire matched expression
    for pattern in SECRET_PATTERNS:
        def redact_callback(match: re.Match) -> str:
            nonlocal red_counter
            red_id = f"RED-{red_counter:03d}"
            placeholder = f"[REDACTED_SECRET_{red_counter:03d}]"

            safety_events.append(
                SafetyEvent(
                    id=red_id,
                    kind=SafetyEventKind.REDACTION,
                    safe_label="Sensitive secret data redacted",
                    segment_id=segment_id,
                )
            )
            safety_event_ids.append(red_id)
            if SafetyFlag.SECRET_REDACTED not in safety_flags:
                safety_flags.append(SafetyFlag.SECRET_REDACTED)

            red_counter += 1
            return placeholder

        sanitized_text = pattern.sub(redact_callback, sanitized_text)

    # Enforce strict 2000 character limit on segment after redaction (no silent truncation)
    # Effectively restricts MVP input to 2,000 sanitized characters since multi-segment splitting is deferred.
    if len(sanitized_text) > 2000:
        raise ValueError(
            f"Sanitized text exceeds single segment limit of 2,000 characters "
            f"(length: {len(sanitized_text)} characters). Multi-segment splitting is deferred."
        )

    # 2. Detect URLs (detected and flagged but not redacted)
    if URL_PATTERN.search(sanitized_text):
        sig_id = f"SIG-{sig_counter:03d}"
        safety_events.append(
            SafetyEvent(
                id=sig_id,
                kind=SafetyEventKind.SIGNAL,
                safe_label="URL Detected",
                segment_id=segment_id,
            )
        )
        safety_event_ids.append(sig_id)
        safety_flags.append(SafetyFlag.URL_DETECTED)
        sig_counter += 1

    # 3. Detect Prompt Injection Phrases
    for pattern in INJECTION_PATTERNS:
        if pattern.search(sanitized_text):
            sig_id = f"SIG-{sig_counter:03d}"
            safety_events.append(
                SafetyEvent(
                    id=sig_id,
                    kind=SafetyEventKind.SIGNAL,
                    safe_label="Prompt Injection Suspected",
                    segment_id=segment_id,
                )
            )
            safety_event_ids.append(sig_id)
            safety_flags.append(SafetyFlag.INJECTION_SUSPECTED)
            sig_counter += 1
            break

    # 4. Detect Unsafe Action Requests
    for pattern in UNSAFE_ACTION_PATTERNS:
        if pattern.search(sanitized_text):
            sig_id = f"SIG-{sig_counter:03d}"
            safety_events.append(
                SafetyEvent(
                    id=sig_id,
                    kind=SafetyEventKind.SIGNAL,
                    safe_label="Unsafe Action Requested",
                    segment_id=segment_id,
                )
            )
            safety_event_ids.append(sig_id)
            safety_flags.append(SafetyFlag.UNSAFE_ACTION_REQUEST)
            sig_counter += 1
            break

    # Create segment
    segment = SanitizedSegment(
        id=segment_id,
        order=1,
        text=sanitized_text,
        safety_flags=safety_flags,
        safety_event_ids=safety_event_ids,
    )

    return SanitizedInputEnvelope(
        segments=[segment],
        safety_events=safety_events,
    )
