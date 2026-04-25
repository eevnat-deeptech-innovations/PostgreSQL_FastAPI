import json
import os
import boto3

s3      = boto3.client("s3")
BUCKET  = os.environ["BUCKET_NAME"]

def lambda_handler(event, context):
    try:
        body    = json.loads(event.get("body", "{}"))
        trip_id = body.get("tripId")

        if not trip_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "tripId is required"})
            }

        # Save full trip metadata from Guidewire to S3
        s3.put_object(
            Bucket=BUCKET,
            Key=f"trips/{trip_id}.json",
            Body=json.dumps(body).encode("utf-8"),
            ContentType="application/json"
        )

        # Also save IMEI → tripId mapping
        imei = body.get("vehicle", {}).get("imei")
        if imei:
            s3.put_object(
                Bucket=BUCKET,
                Key=f"imei-map/{imei}.json",
                Body=json.dumps({"tripId": trip_id, "status": "ACTIVE"}).encode(),
                ContentType="application/json"
            )

        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "STARTED",
                "tripId": trip_id,
                "message": "Trip start recorded"
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
