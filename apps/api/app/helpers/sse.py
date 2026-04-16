import json
import logging
from collections.abc import AsyncIterator

from openai import APIStatusError, RateLimitError

logger = logging.getLogger(__name__)

def encode_sse_event(event_type: str, event_data: dict) -> str:
    return (
        f"event: {event_type}\n"
        f"data: {json.dumps(event_data, separators=(',', ':'))}\n\n"
    )

async def encode_stream_events(events) -> AsyncIterator[str]:
    try:
        async for event in events:
            event_type = str(event["type"])
            event_data = {key: value for key, value in event.items() if key != "type"}
            # SSE uses the `event:` field for routing and the `data:` field for
            # the JSON payload, so avoid duplicating `type` inside the payload.
            yield (
                encode_sse_event(event_type, event_data)
            )
    except RateLimitError:
        logger.warning("OpenAI rate limit or quota issue during stream")
        yield encode_sse_event("error", {
            "message": "Summary generation is temporarily unavailable due to an OpenAI quota or rate limit issue.",
        })
    except APIStatusError:
        logger.exception("OpenAI API status error during stream")
        yield encode_sse_event("error", {
            "message": "Summary generation failed because the upstream AI service returned an error.",
        })
    except Exception:
        logger.exception("Unexpected summary stream failure")
        yield encode_sse_event("error", {
            "message": "Summary generation failed unexpectedly.",
        })
