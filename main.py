from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

PG_DSN = os.getenv("PG_DSN")
if not PG_DSN:
    raise ValueError("PG_DSN is not set. Make sure your .env file exists and contains PG_DSN.")

engine = create_engine(PG_DSN)

app = FastAPI(title="EEVNAT Trip Analytics API", version="1.0")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/trips/{trip_id}/summary")
def get_trip_summary(trip_id: str):
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT * FROM trip_summary WHERE trip_id = :tid"),
            {"tid": trip_id}
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
    return dict(row)

@app.get("/riders/{rider_id}/daily-summary")
def get_daily_summary(rider_id: str, date: str):
    with engine.begin() as conn:
        row = conn.execute(
            text("""
                SELECT * FROM daily_rider_summary
                 WHERE rider_id = :rid AND summary_date = :d
            """),
            {"rid": rider_id, "d": date}
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail=f"No summary for {rider_id} on {date}")
    return dict(row)

@app.get("/riders/{rider_id}/trips")
def get_rider_trips(rider_id: str, date: Optional[str] = None):
    query = "SELECT * FROM trip_summary WHERE rider_id = :rid"
    params = {"rid": rider_id}
    if date:
        query += " AND DATE(start_time) = :date"
        params["date"] = date
    with engine.begin() as conn:
        rows = conn.execute(text(query), params).mappings().all()
    return [dict(r) for r in rows]