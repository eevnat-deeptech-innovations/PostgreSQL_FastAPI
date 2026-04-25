import json
import os
import urllib.request
from datetime import date, timedelta

FASTAPI_URL = os.environ["FASTAPI_BASE_URL"]
GW_URL      = os.environ.get("GUIDEWIRE_DAILY_URL", "")
GW_KEY      = os.environ.get("GUIDEWIRE_API_KEY", "")

# Add all your rider IDs here
RIDER_IDS = [
    "RIDER-ACC-001", "RIDER-ACC-002", "RIDER-ACC-003",
    "RIDER-ACC-004", "RIDER-ACC-005", "RIDER-ACC-006",
    "RIDER-ACC-007", "RIDER-ACC-008", "RIDER-ACC-009",
    "RIDER-ACC-010"
]

def http_get(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

def http_post(url, data):
    if not url:
        print("No Guidewire URL configured — skipping push")
        return
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": GW_KEY
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def lambda_handler(event, context):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    results   = []

    for rider_id in RIDER_IDS:
        try:
            summary = http_get(
                f"{FASTAPI_URL}/riders/{rider_id}/daily-summary?date={yesterday}"
            )
            payload = {
                "riderId":     rider_id,
                "summaryDate": yesterday,
                "summary":     summary
            }
            http_post(GW_URL, payload)
            results.append({"rider": rider_id, "status": "pushed"})
            print(f"  Pushed daily summary for {rider_id}")
        except Exception as e:
            results.append({"rider": rider_id, "status": "error", "error": str(e)})
            print(f"  Error for {rider_id}: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps({"date": yesterday, "results": results})
    }
