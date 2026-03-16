SUMMARY_INSTRUCTIONS = (
    "You are a helpful assistant that summarizes YouTube video transcripts. "
    "Write a concise summary that captures the main ideas, key takeaways, and "
    "important context. Prefer crisp paragraphs over filler."
)


def build_summary_prompt(transcript_text: str) -> str:
    return f"Summarize this transcript:\n\n{transcript_text}"
