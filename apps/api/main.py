import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from app.clients.db import get_db, init_db
from app.clients.openai_client import create_openai_client
from app.config import get_allowed_origin_regex, get_allowed_origins
from app.dependencies.auth import auth_service, get_current_user
from app.helpers.auth import build_user_response
from app.repositories.summaries_repository import SummariesRepository
from app.repositories.transcripts_repository import TranscriptsRepository
from app.schemas.auth import (
    AuthResponse,
    CurrentUserResponse,
    DevLoginRequest,
    GoogleAuthRequest,
)
from app.schemas.summarize import SummarizeRequest, SummarizeResponse
from app.services.auth import AuthenticationError, AuthorizationError
from app.services.summarize_orchestrator import SummarizeOrchestrator
from app.services.summary import SummaryService
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import APIStatusError, RateLimitError
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).resolve().parent / ".env")

summary_service = SummaryService(client=create_openai_client())
transcripts_repository = TranscriptsRepository()
summaries_repository = SummariesRepository()
summarize_orchestrator = SummarizeOrchestrator(
    summary_service=summary_service,
    transcripts_repository=transcripts_repository,
    summaries_repository=summaries_repository,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Ensure the database schema exists before serving requests
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_origin_regex=get_allowed_origin_regex(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    logger.info("Root health check requested")
    return {"message": "Hello World"}


@app.post("/auth/google", response_model=AuthResponse)
async def authenticate_with_google(
    payload: GoogleAuthRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    logger.info("Google auth requested")
    try:
        user = auth_service.authenticate_google_user(db, payload.id_token)
    except AuthorizationError as exc:
        logger.warning("Google auth rejected: %s", exc)
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except AuthenticationError as exc:
        logger.warning("Google auth failed authentication: %s", exc)
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    logger.info("Google auth succeeded for email=%s user_id=%s", user.email, user.id)
    issued_token = auth_service.issue_access_token(user)
    return AuthResponse(
        access_token=issued_token.access_token,
        expires_at=issued_token.expires_at,
        token_type="bearer",
        user=build_user_response(user),
    )


if auth_service.dev_login_enabled:

    @app.post("/auth/dev-login", response_model=AuthResponse)
    async def dev_login(
        payload: DevLoginRequest,
        db: Session = Depends(get_db),
    ) -> AuthResponse:
        logger.info("Dev login requested for email=%s", payload.email or "<default>")
        try:
            user = auth_service.authenticate_dev_user(db, payload.email)
        except AuthenticationError as exc:
            logger.warning("Dev login failed authentication: %s", exc)
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        logger.info("Dev login succeeded for email=%s user_id=%s", user.email, user.id)
        issued_token = auth_service.issue_access_token(user)
        return AuthResponse(
            access_token=issued_token.access_token,
            expires_at=issued_token.expires_at,
            token_type="bearer",
            user=build_user_response(user),
        )


@app.get("/me", response_model=CurrentUserResponse)
async def me(current_user=Depends(get_current_user)) -> CurrentUserResponse:
    logger.info(
        "Current user requested for email=%s user_id=%s",
        current_user.email,
        current_user.id,
    )
    return CurrentUserResponse(user=build_user_response(current_user))


async def encode_stream_events(events) -> AsyncIterator[str]:
    try:
        async for event in events:
            event_type = str(event["type"])
            event_data = {key: value for key, value in event.items() if key != "type"}
            # SSE uses the `event:` field for routing and the `data:` field for
            # the JSON payload, so avoid duplicating `type` inside the payload.
            yield (
                f"event: {event_type}\n"
                f"data: {json.dumps(event_data, separators=(',', ':'))}\n\n"
            )
    except RateLimitError:
        logger.warning("OpenAI rate limit or quota issue during stream")
        yield (
            "event: error\n"
            "data: "
            + json.dumps(
                {
                    "message": "Summary generation is temporarily unavailable due to an OpenAI quota or rate limit issue.",
                },
                separators=(",", ":"),
            )
            + "\n\n"
        )
    except APIStatusError:
        logger.exception("OpenAI API status error during stream")
        yield (
            "event: error\n"
            "data: "
            + json.dumps(
                {
                    "message": "Summary generation failed because the upstream AI service returned an error.",
                },
                separators=(",", ":"),
            )
            + "\n\n"
        )
    except Exception:
        logger.exception("Unexpected summary stream failure")
        yield (
            "event: error\n"
            "data: "
            + json.dumps(
                {"message": "Summary generation failed unexpectedly."},
                separators=(",", ":"),
            )
            + "\n\n"
        )


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    payload: SummarizeRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SummarizeResponse:
    logger.info(
        "Summarize requested for video_id=%s by email=%s user_id=%s",
        payload.video_id,
        current_user.email,
        current_user.id,
    )
    try:
        # Keep the route thin and delegate cache-or-generate logic to the orchestrator
        result = await summarize_orchestrator.summarize_video(db, payload.video_id)
    except RateLimitError as exc:
        logger.warning("OpenAI rate limit or quota issue: %s", exc)
        raise HTTPException(
            status_code=429,
            detail="Summary generation is temporarily unavailable due to an OpenAI quota or rate limit issue.",
        ) from exc
    except APIStatusError as exc:
        logger.exception("OpenAI API status error")
        raise HTTPException(
            status_code=502,
            detail="Summary generation failed because the upstream AI service returned an error.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected summary generation failure")
        raise HTTPException(
            status_code=500,
            detail="Summary generation failed unexpectedly.",
        ) from exc

    logger.info(
        "Summarize completed for video_id=%s by email=%s user_id=%s cached=%s prompt_version=%s",
        payload.video_id,
        current_user.email,
        current_user.id,
        result.cached,
        result.prompt_version,
    )
    return SummarizeResponse(
        summary=result.summary,
        cached=result.cached,
        prompt_version=result.prompt_version,
    )


@app.post("/summarize/stream")
async def summarize_stream(
    payload: SummarizeRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    logger.info(
        "Summarize stream requested for video_id=%s by email=%s user_id=%s",
        payload.video_id,
        current_user.email,
        current_user.id,
    )
    events = summarize_orchestrator.stream_summarize_video(db, payload.video_id)
    return StreamingResponse(
        encode_stream_events(events),
        media_type="text/event-stream",
    )
