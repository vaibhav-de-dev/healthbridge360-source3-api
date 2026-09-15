from __future__ import annotations

import os
import random
from datetime import datetime, timedelta
from typing import Any

from fastapi import FastAPI

APP_NAME = "HealthBridge360 Source 3 API"
APP_VERSION = "2.0.0"
EVENT_COUNT = int(os.getenv("HB360_API_EVENT_COUNT", "2500"))
SEED = int(os.getenv("HB360_API_SEED", "36009"))
SCHEMA_V2_RATE = float(os.getenv("HB360_API_SCHEMA_V2_RATE", "0.60"))
SOURCE_SYSTEM = os.getenv("HB360_API_SOURCE_SYSTEM", "HEALTHBRIDGE360_EVENT_PLATFORM")

EVENT_CATEGORIES = ("CLAIMS", "MEMBER", "ELIGIBILITY", "AUTHORIZATION", "BILLING")
EVENT_TYPES = (
    "CLAIM_CREATED", "CLAIM_UPDATED", "MEMBER_REGISTERED", "MEMBER_UPDATED",
    "ELIGIBILITY_VERIFIED", "AUTHORIZATION_REQUESTED",
    "AUTHORIZATION_APPROVED", "PAYMENT_POSTED", "PAYMENT_REVERSED",
)
EVENT_STATUSES = ("NEW", "UPDATED", "APPROVED", "PENDING", "CANCELLED", "COMPLETED")
DIAGNOSIS_CODES = ("E119","I10","J449","M545","E785","K219","N390","F329","G439","Z0000")
PROCEDURE_CODES = ("99213","99214","99215","80053","85025","93000","81001","36415","71046","70450")
POLICY_TYPES = ("HMO","PPO","EPO","POS")
PAYMENT_METHODS = ("ACH","EFT","CHECK","CARD")
SPECIALTIES = ("CARDIOLOGY","ENDOCRINOLOGY","ORTHOPEDICS","GENERAL_MEDICINE","DERMATOLOGY","NEUROLOGY","ONCOLOGY","PEDIATRICS")
PAYER_NAMES = ("HealthBridge Insurance","Blue Horizon Health","National Care Assurance","Prime Medical Benefits")
HOSPITALS = (
    ("FAC00001","Mumbai Central Medical Center","Mumbai","MH"),
    ("FAC00002","Harborview Health Hospital","Navi Mumbai","MH"),
    ("FAC00003","Lakeside General Hospital","Pune","MH"),
    ("FAC00004","MetroCare Medical Center","Thane","MH"),
    ("FAC00005","Sunrise Specialty Hospital","Mumbai","MH"),
    ("FAC00006","Cedar Valley Medical Center","Bengaluru","KA"),
    ("FAC00007","Riverside General Hospital","Delhi","DL"),
    ("FAC00008","NorthStar Health Center","Hyderabad","TS"),
)
FIRST_NAMES = ("Aarav","Ishaan","Kabir","Vihaan","Arjun","Aanya","Anaya","Diya","Ira","Myra")
LAST_NAMES = ("Sharma","Patel","Mehta","Desai","Kulkarni","Joshi","Iyer","Rao","Kapoor","Nair")

app = FastAPI(title=APP_NAME, version=APP_VERSION)

def money(rng: random.Random, low=50, high=5000):
    return round(rng.uniform(low, high), 2)

def member(rng, n):
    return {
        "member_id": f"MBR{n:09d}",
        "legacy_member_id": f"LM{n:07d}",
        "demographics": {
            "first_name": rng.choice(FIRST_NAMES),
            "last_name": rng.choice(LAST_NAMES),
            "date_of_birth": f"{rng.randint(1950,2002)}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
            "gender": rng.choice(("M","F","U")),
            "state": rng.choice(("MH","KA","DL","TS","GJ","TN")),
        },
        "contact": {"postal_code": f"{rng.randint(400000,799999)}", "country": "IN"},
    }

def provider(rng, n):
    f = rng.choice(HOSPITALS)
    return {
        "provider_id": f"PRV{n:08d}",
        "provider_type": rng.choice(("PHYSICIAN","HOSPITAL","LAB","PHARMACY")),
        "specialty": rng.choice(SPECIALTIES),
        "facility": {
            "facility_id": f[0], "facility_name": f[1],
            "city": f[2], "state": f[3],
        },
    }

def insurance(rng, n):
    return {
        "policy_id": f"POL{n:09d}",
        "payer": rng.choice(PAYER_NAMES),
        "plan_type": rng.choice(POLICY_TYPES),
        "coverage": {
            "level": rng.choice(("INDIVIDUAL","FAMILY","SPOUSE","CHILD")),
            "in_network": rng.choice((True,True,True,False)),
        },
    }

def payload(rng, category, n, version):
    if category == "CLAIMS":
        claim_id = f"CLM{rng.randint(1,1200000):09d}"
        if version == 1:
            return {
                "claim_id": claim_id,
                "claim_amount": money(rng),
                "claim_status": rng.choice(("SUBMITTED","APPROVED","DENIED","PAID")),
                "procedure_code": rng.choice(PROCEDURE_CODES),
            }
        return {
            "claim": {
                "id": claim_id,
                "amount": money(rng),
                "currency": "INR",
                "status": rng.choice(("SUBMITTED","APPROVED","DENIED","PAID")),
                "service": {
                    "procedure_code": rng.choice(PROCEDURE_CODES),
                    "place_of_service": rng.choice(("OFFICE","INPATIENT_HOSPITAL","OUTPATIENT_HOSPITAL","EMERGENCY_ROOM","LABORATORY")),
                    "diagnosis_codes": [rng.choice(DIAGNOSIS_CODES), rng.choice(DIAGNOSIS_CODES)],
                },
            },
            "provider_claim_context": {
                "network_status": rng.choice(("IN_NETWORK","OUT_OF_NETWORK")),
                "referral_required": rng.choice((True,False)),
            },
        }

    if category == "ELIGIBILITY":
        status = rng.choice(("ELIGIBLE","ELIGIBLE","ELIGIBLE","INELIGIBLE"))
        if version == 1:
            return {"eligibility_status": status, "policy_id": f"POL{n:09d}", "effective_date": "2021-01-01"}
        return {
            "eligibility": {
                "status": status,
                "policy": {"policy_id": f"POL{n:09d}", "coverage_start": "2021-01-01", "coverage_end": None},
                "benefits": {"medical": True, "pharmacy": rng.choice((True,True,False)), "dental": rng.choice((True,False))},
            }
        }

    if category == "AUTHORIZATION":
        decision = rng.choice(("PENDING","APPROVED","DENIED"))
        if version == 1:
            return {"authorization_id": f"AUTH{n:08d}", "decision": decision, "requested_service": rng.choice(PROCEDURE_CODES)}
        return {
            "authorization": {
                "authorization_id": f"AUTH{n:08d}",
                "decision": decision,
                "requested_service": {"procedure_code": rng.choice(PROCEDURE_CODES), "units": rng.randint(1,5)},
                "clinical_review": {"review_required": rng.choice((True,False)), "review_outcome": rng.choice(("STANDARD","CLINICAL_REVIEW"))},
            }
        }

    if category == "BILLING":
        amount = money(rng, 50, 4500)
        if version == 1:
            return {"payment_id": f"PAY{n:09d}", "payment_amount": amount, "payment_status": rng.choice(("PAID","PENDING","FAILED")), "payment_method": rng.choice(PAYMENT_METHODS)}
        return {
            "billing": {
                "payment": {"payment_id": f"PAY{n:09d}", "amount": amount, "currency": "INR", "status": rng.choice(("PAID","PENDING","FAILED"))},
                "settlement": {"method": rng.choice(PAYMENT_METHODS), "reconciliation_status": rng.choice(("MATCHED","PENDING","EXCEPTION"))},
            }
        }

    return {
        "member_activity": {
            "activity": rng.choice(("PROFILE_UPDATED","CONTACT_UPDATED","DEMOGRAPHICS_UPDATED")),
            "change_reason": rng.choice(("MEMBER_REQUEST","SOURCE_UPDATE","SYSTEM_PROCESS")),
        }
    }

def generate():
    rng = random.Random(SEED)
    base = datetime(2019,1,1)
    result = []
    for i in range(1, EVENT_COUNT + 1):
        category = rng.choice(EVENT_CATEGORIES)
        version = 2 if rng.random() < SCHEMA_V2_RATE else 1
        n = rng.randint(1,100000)
        event_time = base + timedelta(days=rng.randint(0,1095), seconds=rng.randint(0,86399))
        result.append({
            "event_id": f"EVT{i:010d}",
            "event_type": rng.choice(EVENT_TYPES),
            "event_category": category,
            "schema_version": f"v{version}",
            "event_timestamp": event_time.isoformat(),
            "source_system": SOURCE_SYSTEM,
            "source_region": "ap-south-1",
            "correlation_id": f"CORR{rng.randint(1,99999999):08d}",
            "trace": {
                "producer": rng.choice(("claims-service","membership-service","eligibility-service","authorization-service","billing-service")),
                "producer_version": rng.choice(("3.1.0","3.2.0","4.0.0")),
                "delivery_attempt": rng.randint(1,3),
            },
            "member": member(rng, n),
            "provider": provider(rng, rng.randint(1,50000)),
            "insurance": insurance(rng, n),
            "event_context": {
                "status": rng.choice(EVENT_STATUSES),
                "priority": rng.choice(("LOW","NORMAL","HIGH")),
                "environment": "production-simulated",
            },
            "payload": payload(rng, category, n, version),
        })
    return result

EVENTS = generate()

@app.get("/")
def root():
    return {"service": APP_NAME, "status": "UP", "version": APP_VERSION, "event_count": len(EVENTS), "events_endpoint": "/events", "health_endpoint": "/health"}

@app.get("/health")
def health():
    return {"status": "UP", "service": APP_NAME, "event_count": len(EVENTS)}

@app.get("/events")
def events():
    return {
        "api_version": APP_VERSION,
        "source_system": SOURCE_SYSTEM,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_events": len(EVENTS),
        "schema_distribution": {
            "v1": sum(e["schema_version"] == "v1" for e in EVENTS),
            "v2": sum(e["schema_version"] == "v2" for e in EVENTS),
        },
        "events": EVENTS,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT","10000")))
