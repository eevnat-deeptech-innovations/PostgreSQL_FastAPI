import json
import os
import boto3
import urllib.request

s3           = boto3.client("s3")
BUCKET       = os.environ["BUCKET_NAME"]
FASTAPI_URL  = os.environ["FASTAPI_BASE_URL"]
GW_URL       = os.environ.get("GUIDEWIRE_PUSH_URL", "")
GW_KEY       = os.environ.get("GUIDEWIRE_API_KEY", "")

def fetch_trip_summary(trip_id):
    url = f"{FASTAPI_URL}/trips/{trip_id}/summary"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

def push_to_guidewire(payload):
    if not GW_URL:
        print("GUIDEWIRE_PUSH_URL not set — skipping push")
        return
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        GW_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": GW_KEY
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def lambda_handler(event, context):
    try:
        body         = json.loads(event.get("body", "{}"))
        trip_id      = body.get("tripId")
        incident     = body.get("incidentFlag", False)
        claim_id     = body.get("claimId")

        if not trip_id:
            return {"statusCode": 400, "body": json.dumps({"error": "tripId required"})}

        # Fetch analysed summary from FastAPI
        try:
            summary = fetch_trip_summary(trip_id)
        except Exception as e:
            summary = {"error": f"Summary not yet available: {str(e)}"}

        # Save the summary to S3 for record-keeping
        s3.put_object(
            Bucket=BUCKET,
            Key=f"trips/{trip_id}_summary.json",
            Body=json.dumps(summary).encode("utf-8"),
            ContentType="application/json"
        )

        # If incident or claim — push to Guidewire immediately
        if incident or claim_id:
            payload = {
                "claimId":  claim_id,
                "tripId":   trip_id,
                "telematics": summary
            }
            try:
                push_to_guidewire(payload)
                print(f"Incident push sent for trip {trip_id}")
            except Exception as e:
                print(f"Guidewire push failed: {e}")

        return {
            "statusCode": 202,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "COMPLETED",
                "tripId": trip_id,
                "riskScore": summary.get("dynamic_risk_score"),
                "incidentPushed": bool(incident or claim_id)
            })
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
