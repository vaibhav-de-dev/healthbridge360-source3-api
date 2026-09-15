from __future__ import annotations

import os
import random
from datetime import datetime, timedelta
from typing import Any

from fastapi import FastAPI, HTTPException

APP_NAME = "HealthBridge360 Source 3 API"
APP_VERSION = "3.0.0"

EVENT_COUNT = int(os.getenv("HB360_API_EVENT_COUNT", "2500"))
SEED = int(os.getenv("HB360_API_SEED", "36009"))
SCHEMA_V2_RATE = float(os.getenv("HB360_API_SCHEMA_V2_RATE", "0.60"))

# Source 3 DQ scenario rates. Keep them configurable so the generator scales
# without code changes.
NULL_RATE = float(os.getenv("HB360_API_NULL_RATE", "0.02"))
WHITESPACE_RATE = float(os.getenv("HB360_API_WHITESPACE_RATE", "0.02"))
CASE_VARIATION_RATE = float(os.getenv("HB360_API_CASE_VARIATION_RATE", "0.02"))
INVALID_VALUE_RATE = float(os.getenv("HB360_API_INVALID_VALUE_RATE", "0.01"))
MISSING_CRITICAL_ID_RATE = float(os.getenv("HB360_API_MISSING_CRITICAL_ID_RATE", "0.005"))
BAD_DATE_RATE = float(os.getenv("HB360_API_BAD_DATE_RATE", "0.003"))
FUTURE_TIMESTAMP_RATE = float(os.getenv("HB360_API_FUTURE_TIMESTAMP_RATE", "0.003"))
TIMESTAMP_FORMAT_VARIATION_RATE = float(
    os.getenv("HB360_API_TIMESTAMP_FORMAT_VARIATION_RATE", "0.005")
)
DUPLICATE_RATE = float(os.getenv("HB360_API_DUPLICATE_RATE", "0.01"))
LATE_ARRIVAL_RATE = float(os.getenv("HB360_API_LATE_ARRIVAL_RATE", "0.02"))
ORPHAN_REFERENCE_RATE = float(os.getenv("HB360_API_ORPHAN_REFERENCE_RATE", "0.005"))
API_FAILURE_RATE = float(os.getenv("HB360_API_FAILURE_RATE", "0.00"))

SOURCE_SYSTEM = os.getenv(
    "HB360_API_SOURCE_SYSTEM",
    "HEALTHBRIDGE360_EVENT_PLATFORM",
)

EVENT_CATEGORIES = (
    "CLAIMS",
    "MEMBER",
    "ELIGIBILITY",
    "AUTHORIZATION",
    "BILLING",
)
EVENT_TYPES = (
    "CLAIM_CREATED",
    "CLAIM_UPDATED",
    "MEMBER_REGISTERED",
    "MEMBER_UPDATED",
    "ELIGIBILITY_VERIFIED",
    "AUTHORIZATION_REQUESTED",
    "AUTHORIZATION_APPROVED",
    "PAYMENT_POSTED",
    "PAYMENT_REVERSED",
)
EVENT_STATUSES = (
    "NEW",
    "UPDATED",
    "APPROVED",
    "PENDING",
    "CANCELLED",
    "COMPLETED",
)
DIAGNOSIS_CODES = (
    "E119",
    "I10",
    "J449",
    "M545",
    "E785",
    "K219",
    "N390",
    "F329",
    "G439",
    "Z0000",
)
PROCEDURE_CODES = (
    "99213",
    "99214",
    "99215",
    "80053",
    "85025",
    "93000",
    "81001",
    "36415",
    "71046",
    "70450",
)
POLICY_TYPES = ("HMO", "PPO", "EPO", "POS")
PAYMENT_METHODS = ("ACH", "EFT", "CHECK", "CARD")
SPECIALTIES = (
    "CARDIOLOGY",
    "ENDOCRINOLOGY",
    "ORTHOPEDICS",
    "GENERAL_MEDICINE",
    "DERMATOLOGY",
    "NEUROLOGY",
    "ONCOLOGY",
    "PEDIATRICS",
)
PAYER_NAMES = (
    "HealthBridge Insurance",
    "Blue Horizon Health",
    "National Care Assurance",
    "Prime Medical Benefits",
)
HOSPITALS = (
    ("FAC00001", "Mumbai Central Medical Center", "Mumbai", "MH"),
    ("FAC00002", "Harborview Health Hospital", "Navi Mumbai", "MH"),
    ("FAC00003", "Lakeside General Hospital", "Pune", "MH"),
    ("FAC00004", "MetroCare Medical Center", "Thane", "MH"),
    ("FAC00005", "Sunrise Specialty Hospital", "Mumbai", "MH"),
    ("FAC00006", "Cedar Valley Medical Center", "Bengaluru", "KA"),
    ("FAC00007", "Riverside General Hospital", "Delhi", "DL"),
    ("FAC00008", "NorthStar Health Center", "Hyderabad", "TS"),
)
FIRST_NAMES = (
    "Aarav", "Ishaan", "Kabir", "Vihaan", "Arjun",
    "Aanya", "Anaya", "Diya", "Ira", "Myra",
)
LAST_NAMES = (
    "Sharma", "Patel", "Mehta", "Desai", "Kulkarni",
    "Joshi", "Iyer", "Rao", "Kapoor", "Nair",
)

app = FastAPI(title=APP_NAME, version=APP_VERSION)


def _maybe_null(value: Any, rng: random.Random) -> Any:
    return None if rng.random() < NULL_RATE else value


def _maybe_whitespace(value: Any, rng: random.Random) -> Any:
    if not isinstance(value, str):
        return value
    if rng.random() >= WHITESPACE_RATE:
        return value
    style = rng.choice(("leading", "trailing", "both", "internal"))
    if style == "leading":
        return f"  {value}"
    if style == "trailing":
        return f"{value}  "
    if style == "both":
        return f"  {value}  "
    if len(value) > 3:
        midpoint = len(value) // 2
        return value[:midpoint] + " " + value[midpoint:]
    return value


def _maybe_case(value: Any, rng: random.Random) -> Any:
    if not isinstance(value, str):
        return value
    if rng.random() >= CASE_VARIATION_RATE:
        return value
    return rng.choice(
        (
            value.lower(),
            value.upper(),
            value.title(),
        )
    )


def _string(value: str, rng: random.Random) -> str | None:
    value = _maybe_whitespace(value, rng)
    value = _maybe_case(value, rng)
    if rng.random() < NULL_RATE:
        return None
    return value


def _money(rng: random.Random, low=50, high=5000) -> float:
    value = round(rng.uniform(low, high), 2)
    if rng.random() < INVALID_VALUE_RATE:
        return -abs(value)
    return value


def _timestamp(rng: random.Random) -> str:
    base = datetime(2019, 1, 1)
    event_time = base + timedelta(
        days=rng.randint(0, 1095),
        seconds=rng.randint(0, 86399),
    )

    if rng.random() < FUTURE_TIMESTAMP_RATE:
        event_time = datetime.utcnow() + timedelta(days=rng.randint(1, 120))

    if rng.random() < BAD_DATE_RATE:
        return rng.choice(
            (
                "2021-13-45T25:99:99",
                "not-a-timestamp",
                "2021/99/99 25:61:61",
            )
        )

    stamp = event_time.isoformat()

    if rng.random() < TIMESTAMP_FORMAT_VARIATION_RATE:
        return rng.choice(
            (
                stamp.replace("T", " "),
                stamp.split(".")[0] + "Z",
                stamp + "+05:30",
            )
        )

    return stamp


def _member(rng: random.Random, member_number: int) -> dict[str, Any]:
    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)

    member_id = (
        f"MBR{member_number:09d}"
        if rng.random() >= MISSING_CRITICAL_ID_RATE
        else None
    )

    if rng.random() < ORPHAN_REFERENCE_RATE:
        member_id = f"MBR999999999"

    return {
        "member_id": member_id,
        "legacy_member_id": _maybe_null(
            f"LM{member_number:07d}",
            rng,
        ),
        "demographics": {
            "first_name": _string(first, rng),
            "last_name": _string(last, rng),
            "date_of_birth": _maybe_null(
                f"{rng.randint(1950, 2002)}-"
                f"{rng.randint(1, 12):02d}-"
                f"{rng.randint(1, 28):02d}",
                rng,
            ),
            "gender": _string(
                rng.choice(("M", "F", "U")),
                rng,
            ),
            "state": _string(
                rng.choice(("MH", "KA", "DL", "TS", "GJ", "TN")),
                rng,
            ),
        },
        "contact": {
            "postal_code": _string(
                str(rng.randint(400000, 799999)),
                rng,
            ),
            "country": "IN",
        },
    }


def _provider(rng: random.Random, provider_number: int) -> dict[str, Any]:
    facility = rng.choice(HOSPITALS)

    provider_id = (
        f"PRV{provider_number:08d}"
        if rng.random() >= MISSING_CRITICAL_ID_RATE
        else None
    )

    if rng.random() < ORPHAN_REFERENCE_RATE:
        provider_id = "PRV99999999"

    return {
        "provider_id": provider_id,
        "provider_type": _string(
            rng.choice(("PHYSICIAN", "HOSPITAL", "LAB", "PHARMACY")),
            rng,
        ),
        "specialty": _string(
            rng.choice(SPECIALTIES),
            rng,
        ),
        "facility": {
            "facility_id": _string(facility[0], rng),
            "facility_name": _string(facility[1], rng),
            "city": _string(facility[2], rng),
            "state": _string(facility[3], rng),
        },
    }


def _insurance(rng: random.Random, member_number: int) -> dict[str, Any]:
    return {
        "policy_id": _string(
            f"POL{member_number:09d}",
            rng,
        ),
        "payer": _string(
            rng.choice(PAYER_NAMES),
            rng,
        ),
        "plan_type": _string(
            rng.choice(POLICY_TYPES),
            rng,
        ),
        "coverage": {
            "level": _string(
                rng.choice(("INDIVIDUAL", "FAMILY", "SPOUSE", "CHILD")),
                rng,
            ),
            "in_network": rng.choice((True, True, True, False)),
        },
    }


def _claim_payload(
    rng: random.Random,
    claim_number: int,
    version: int,
) -> dict[str, Any]:
    claim_id = f"CLM{claim_number:09d}"

    if version == 1:
        return {
            "claim_id": _string(claim_id, rng),
            "claim_amount": _money(rng),
            "claim_status": _string(
                rng.choice(("SUBMITTED", "APPROVED", "DENIED", "PAID")),
                rng,
            ),
            "procedure_code": _string(
                rng.choice(PROCEDURE_CODES),
                rng,
            ),
        }

    return {
        "claim": {
            "id": _string(claim_id, rng),
            "amount": _money(rng),
            "currency": "INR",
            "status": _string(
                rng.choice(("SUBMITTED", "APPROVED", "DENIED", "PAID")),
                rng,
            ),
            "service": {
                "procedure_code": _string(
                    rng.choice(PROCEDURE_CODES),
                    rng,
                ),
                "place_of_service": _string(
                    rng.choice(
                        (
                            "OFFICE",
                            "INPATIENT_HOSPITAL",
                            "OUTPATIENT_HOSPITAL",
                            "EMERGENCY_ROOM",
                            "LABORATORY",
                        )
                    ),
                    rng,
                ),
                "diagnosis_codes": [
                    _string(rng.choice(DIAGNOSIS_CODES), rng),
                    _string(rng.choice(DIAGNOSIS_CODES), rng),
                ],
            },
        },
        "provider_claim_context": {
            "network_status": _string(
                rng.choice(("IN_NETWORK", "OUT_OF_NETWORK")),
                rng,
            ),
            "referral_required": rng.choice((True, False)),
        },
    }


def _eligibility_payload(
    rng: random.Random,
    member_number: int,
    version: int,
) -> dict[str, Any]:
    status = rng.choice(("ELIGIBLE", "ELIGIBLE", "ELIGIBLE", "INELIGIBLE"))

    if rng.random() < INVALID_VALUE_RATE:
        status = "UNKNOWN_STATUS"

    if version == 1:
        return {
            "eligibility_status": _string(status, rng),
            "policy_id": _string(f"POL{member_number:09d}", rng),
            "effective_date": "2021-01-01",
        }

    return {
        "eligibility": {
            "status": _string(status, rng),
            "policy": {
                "policy_id": _string(f"POL{member_number:09d}", rng),
                "coverage_start": "2021-01-01",
                "coverage_end": None,
            },
            "benefits": {
                "medical": True,
                "pharmacy": rng.choice((True, True, False)),
                "dental": rng.choice((True, False)),
            },
        }
    }


def _authorization_payload(
    rng: random.Random,
    claim_number: int,
    version: int,
) -> dict[str, Any]:
    decision = rng.choice(("PENDING", "APPROVED", "DENIED"))

    if version == 1:
        return {
            "authorization_id": _string(
                f"AUTH{claim_number:08d}",
                rng,
            ),
            "decision": _string(decision, rng),
            "requested_service": _string(
                rng.choice(PROCEDURE_CODES),
                rng,
            ),
        }

    return {
        "authorization": {
            "authorization_id": _string(
                f"AUTH{claim_number:08d}",
                rng,
            ),
            "decision": _string(decision, rng),
            "requested_service": {
                "procedure_code": _string(
                    rng.choice(PROCEDURE_CODES),
                    rng,
                ),
                "units": (
                    -rng.randint(1, 5)
                    if rng.random() < INVALID_VALUE_RATE
                    else rng.randint(1, 5)
                ),
            },
            "clinical_review": {
                "review_required": rng.choice((True, False)),
                "review_outcome": _string(
                    rng.choice(("STANDARD", "CLINICAL_REVIEW")),
                    rng,
                ),
            },
        }
    }


def _billing_payload(
    rng: random.Random,
    claim_number: int,
    version: int,
) -> dict[str, Any]:
    amount = _money(rng, 50, 4500)

    if version == 1:
        return {
            "payment_id": _string(
                f"PAY{claim_number:09d}",
                rng,
            ),
            "payment_amount": amount,
            "payment_status": _string(
                rng.choice(("PAID", "PENDING", "FAILED")),
                rng,
            ),
            "payment_method": _string(
                rng.choice(PAYMENT_METHODS),
                rng,
            ),
        }

    return {
        "billing": {
            "payment": {
                "payment_id": _string(
                    f"PAY{claim_number:09d}",
                    rng,
                ),
                "amount": amount,
                "currency": "INR",
                "status": _string(
                    rng.choice(("PAID", "PENDING", "FAILED")),
                    rng,
                ),
            },
            "settlement": {
                "method": _string(
                    rng.choice(PAYMENT_METHODS),
                    rng,
                ),
                "reconciliation_status": _string(
                    rng.choice(("MATCHED", "PENDING", "EXCEPTION")),
                    rng,
                ),
            },
        }
    }


def _payload(
    rng: random.Random,
    category: str,
    number: int,
    version: int,
) -> dict[str, Any]:
    if category == "CLAIMS":
        return _claim_payload(rng, rng.randint(1, 1200000), version)

    if category == "ELIGIBILITY":
        return _eligibility_payload(rng, number, version)

    if category == "AUTHORIZATION":
        return _authorization_payload(
            rng,
            rng.randint(1, 1200000),
            version,
        )

    if category == "BILLING":
        return _billing_payload(
            rng,
            rng.randint(1, 1200000),
            version,
        )

    return {
        "member_activity": {
            "activity": _string(
                rng.choice(
                    (
                        "PROFILE_UPDATED",
                        "CONTACT_UPDATED",
                        "DEMOGRAPHICS_UPDATED",
                    )
                ),
                rng,
            ),
            "change_reason": _string(
                rng.choice(
                    (
                        "MEMBER_REQUEST",
                        "SOURCE_UPDATE",
                        "SYSTEM_PROCESS",
                    )
                ),
                rng,
            ),
        }
    }


def generate_events() -> list[dict[str, Any]]:
    rng = random.Random(SEED)
    events: list[dict[str, Any]] = []

    for number in range(1, EVENT_COUNT + 1):
        category = rng.choice(EVENT_CATEGORIES)
        version = 2 if rng.random() < SCHEMA_V2_RATE else 1

        event_id = f"EVT{number:010d}"

        # Intentional duplicate identifier scenario.
        if events and rng.random() < DUPLICATE_RATE:
            event_id = rng.choice(events)["event_id"]

        event = {
            "event_id": event_id,
            "event_type": _string(
                rng.choice(EVENT_TYPES),
                rng,
            ),
            "event_category": _string(
                category,
                rng,
            ),
            "schema_version": f"v{version}",
            "event_timestamp": _timestamp(rng),
            "source_system": _string(
                SOURCE_SYSTEM,
                rng,
            ),
            "source_region": "ap-south-1",
            "correlation_id": _string(
                f"CORR{rng.randint(1, 99999999):08d}",
                rng,
            ),
            "trace": {
                "producer": _string(
                    rng.choice(
                        (
                            "claims-service",
                            "membership-service",
                            "eligibility-service",
                            "authorization-service",
                            "billing-service",
                        )
                    ),
                    rng,
                ),
                "producer_version": _string(
                    rng.choice(("3.1.0", "3.2.0", "4.0.0")),
                    rng,
                ),
                "delivery_attempt": rng.randint(1, 3),
            },
            "member": _member(
                rng,
                rng.randint(1, 100000),
            ),
            "provider": _provider(
                rng,
                rng.randint(1, 50000),
            ),
            "insurance": _insurance(
                rng,
                rng.randint(1, 100000),
            ),
            "event_context": {
                "status": _string(
                    rng.choice(EVENT_STATUSES),
                    rng,
                ),
                "priority": _string(
                    rng.choice(("LOW", "NORMAL", "HIGH")),
                    rng,
                ),
                "environment": "production-simulated",
            },
            "payload": _payload(
                rng,
                category,
                number,
                version,
            ),
        }

        # Preserve obvious out-of-order/late-arriving records.
        if rng.random() < LATE_ARRIVAL_RATE:
            event["trace"]["arrival_delay_hours"] = rng.randint(24, 240)
        else:
            event["trace"]["arrival_delay_hours"] = 0

        # Critical ID can be removed at event level too.
        if rng.random() < MISSING_CRITICAL_ID_RATE:
            event["correlation_id"] = None

        # Intentional invalid category/value scenario.
        if rng.random() < INVALID_VALUE_RATE:
            event["event_category"] = "UNKNOWN_CATEGORY"

        events.append(event)

    return events


EVENTS = generate_events()


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": APP_NAME,
        "status": "UP",
        "version": APP_VERSION,
        "event_count": len(EVENTS),
        "api_model": "single-response-full-event-collection",
        "events_endpoint": "/events",
        "health_endpoint": "/health",
        "dq_scenarios": [
            "nulls",
            "whitespace",
            "case_variation",
            "invalid_values",
            "missing_critical_ids",
            "malformed_dates",
            "future_timestamps",
            "timestamp_format_variations",
            "duplicates",
            "late_arrivals",
            "orphan_references",
            "api_failures",
        ],
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "UP",
        "service": APP_NAME,
        "event_count": len(EVENTS),
    }


@app.get("/events")
def events() -> dict[str, Any]:
    # Optional API-level failure simulation. Keep 0.00 for normal runs.
    failure_rng = random.Random()
    if failure_rng.random() < API_FAILURE_RATE:
        raise HTTPException(
            status_code=503,
            detail="Simulated upstream Source 3 API failure",
        )

    late_arrivals = sum(
        1
        for event in EVENTS
        if event.get("trace", {}).get("arrival_delay_hours", 0) > 0
    )
    duplicate_ids = len(EVENTS) - len(
        {event["event_id"] for event in EVENTS}
    )

    return {
        "api_version": APP_VERSION,
        "source_system": SOURCE_SYSTEM,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_events": len(EVENTS),
        "dq_summary": {
            "late_arrival_records": late_arrivals,
            "duplicate_event_ids": duplicate_ids,
        },
        "schema_distribution": {
            "v1": sum(
                event["schema_version"] == "v1"
                for event in EVENTS
            ),
            "v2": sum(
                event["schema_version"] == "v2"
                for event in EVENTS
            ),
        },
        "events": EVENTS,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "10000")),
    )
