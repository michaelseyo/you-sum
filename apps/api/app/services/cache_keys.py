import hashlib


def normalize_transcript_text(transcript_text: str) -> str:
    # Standardize whitespace so equivalent transcripts hash to the same cache key
    normalized_lines = [
        line.strip() for line in transcript_text.splitlines() if line.strip()
    ]
    return "\n".join(normalized_lines)


def build_transcript_fingerprint(transcript_text: str) -> str:
    # Hash normalized transcript content for stable cache lookups
    normalized_text = normalize_transcript_text(transcript_text)
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
