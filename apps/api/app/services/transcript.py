from youtube_transcript_api import YouTubeTranscriptApi

ytt_api = YouTubeTranscriptApi()


def fetch_transcript_text(video_id: str) -> str:
    fetched_transcript = ytt_api.fetch(video_id)
    transcript_list = fetched_transcript.to_raw_data()
    return "\n".join(entry["text"] for entry in transcript_list)
