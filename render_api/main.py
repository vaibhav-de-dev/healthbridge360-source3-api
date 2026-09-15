
"""
HealthBridge360 - Source 3 Public Web API for Render.

One public base URL:
    https://<service>.onrender.com

Endpoints:
    GET /
    GET /events
    GET /health

The API generates deterministic synthetic healthcare events in memory at
startup, so no local WSL filesystem is required by the deployed service.
The same event model and v1/v2 schema evolution used in Phase 2 are retained.
"""

from __future__ import annotations

import os
import random
from datetime import datetime, timedelta

from fastapi import FastAPI, Query

APP_NAME = "HealthBridge360 Source 3 API"

DEFAULT_EVENT_COUNT = int(
    os.getenv("HB360_API_EVENT_COUNT", "2500")
)

DEFAULT_SEED = int(
    os.getenv("HB360_API_SEED", "36009")
)

SCHEMA_V1_RATE = float(
    os.getenv("HB360_API_SCHEMA_V1_RATE", "0.40")
)

SCHEMA_V2_RATE = 1.0 - SCHEMA_V1_RATE

API_FAILURE_RATE = float(
    os.getenv("HB360_API_FAILURE_RATE", "0.00")
)

PAGE_DEFAULT_SIZE = int(
    os.getenv("HB360_API_PAGE_SIZE", "100")
)

EVENT_CATEGORIES = (
    "CLAIMS",
    "MEMBER",
    "ELIGIBILITY",
    "AUTHORIZATION",
)

EVENT_STATUSES = (
    "NEW",
    "UPDATED",
    "CANCELLED",
)

DIAGNOSIS_CODES = (
    "E119",
    "I10",
    "J449",
    "M545",
    "E785",
    "K219",
    "N390",
)

PROCEDURE_CODES = (
    "99213",
    "99214",
    "99215",
    "80053",
    "85025",
    "93000",
)


def generate_events(
    event_count: int,
    seed: int,
) -> list[dict]:
    """Generate deterministic in-memory Source 3 events."""

    rng = random.Random(seed)

    events: list[dict] = []

    start_datetime = datetime(
        2019,
        1,
        1,
        0,
        0,
        0,
    )

    for number in range(
        1,
        event_count + 1,
    ):
        category = rng.choice(
            EVENT_CATEGORIES
        )

        version = (
            1
            if rng.random() < SCHEMA_V1_RATE
            else 2
        )

        event_time = (
            start_datetime
            + timedelta(
                days=rng.randint(
                    0,
                    3 * 365,
                ),
                seconds=rng.randint(
                    0,
                    86_399,
                ),
            )
        )

        member_id = (
            f"LM{rng.randint(1, 100_000):07d}"
        )

        provider_id = (
            f"PRV{rng.randint(1, 50_000):06d}"
        )

        claim_id = (
            f"CLM{rng.randint(1, 1_200_000):09d}"
        )

        if (
            category == "CLAIMS"
            and version == 2
        ):
            payload = {
                "claim": {
                    "id": claim_id,
                    "amount": round(
                        rng.uniform(
                            50,
                            5_000,
                        ),
                        2,
                    ),
                    "diagnosis_codes": [
                        rng.choice(
                            DIAGNOSIS_CODES
                        ),
                        rng.choice(
                            DIAGNOSIS_CODES
                        ),
                    ],
                    "procedure_code": rng.choice(
                        PROCEDURE_CODES
                    ),
                },
                "provider": {
                    "id": provider_id,
                },
            }

        elif category == "CLAIMS":
            payload = {
                "claim_id": claim_id,
                "claim_amount": round(
                    rng.uniform(
                        50,
                        5_000,
                    ),
                    2,
                ),
                "provider_id": provider_id,
            }

        else:
            payload = {
                "event_type": category,
                "status": rng.choice(
                    EVENT_STATUSES
                ),
                "value": round(
                    rng.uniform(
                        1,
                        1_000,
                    ),
                    2,
                ),
            }

        events.append(
            {
                "event_id": (
                    f"EVT{number:09d}"
                ),
                "member_id": member_id,
                "event_category": category,
                "schema_version": f"v{version}",
                "event_timestamp": event_time.isoformat(),
                "payload": payload,
            }
        )

    return events


EVENTS = generate_events(
    DEFAULT_EVENT_COUNT,
    DEFAULT_SEED,
)

app = FastAPI(
    title=APP_NAME,
    version="1.0.0",
)


@app.get("/")
def root() -> dict:
    """Single documented base URL."""

    return {
        "service": APP_NAME,
        "status": "UP",
        "version": "1.0.0",
        "event_count": len(EVENTS),
        "endpoints": {
            "events": "/events",
            "health": "/health",
        },
        "usage": (
            "Call this base URL with /events?page=1&page_size=100"
        ),
    }


@app.get("/health")
def health() -> dict:
    """Render health endpoint."""

    return {
        "status": "UP",
        "service": APP_NAME,
        "event_count": len(EVENTS),
    }


@app.get("/events")
def events(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=PAGE_DEFAULT_SIZE,
        ge=1,
        le=1000,
    ),
) -> dict:
    """Return paginated healthcare events."""

    start = (
        page - 1
    ) * page_size

    end = start + page_size

    page_events = EVENTS[
        start:end
    ]

    return {
        "page": page,
        "page_size": page_size,
        "total": len(EVENTS),
        "has_next": end < len(EVENTS),
        "events": page_events,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(
        os.getenv(
            "PORT",
            "10000",
        )
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )
