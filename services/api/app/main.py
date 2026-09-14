"""Telemetry intake API.

Implements FR-08 (accept, validate and store telemetry) and the write side of
FR-16 (controller archive re-read after a connection loss). Measurements and
their outbound events are written in a single transaction; publishing to Kafka
is done separately by the outbox relay.
"""

import json
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, Field

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://gas:gas@127.0.0.1:5434/gas_metering"
)

pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=5, open=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    yield
    pool.close()


app = FastAPI(title="Gas metering intake API", lifespan=lifespan)


class Measurement(BaseModel):
    node_code: str
    measured_at: datetime
    flow_rate: float = Field(ge=0)
    pressure: float = Field(gt=0)
    temperature: float
    source: Literal["telemetry", "archive"] = "telemetry"


class MeasurementBatch(BaseModel):
    measurements: list[Measurement] = Field(min_length=1, max_length=1000)


class IntakeResult(BaseModel):
    accepted: int
    duplicates: int


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/measurements", response_model=IntakeResult)
def ingest(batch: MeasurementBatch) -> IntakeResult:
    codes = {m.node_code for m in batch.measurements}

    with pool.connection() as conn:
        conn.row_factory = dict_row

        with conn.transaction():
            rows = conn.execute(
                "SELECT id, code FROM metering_node WHERE code = ANY(%s)",
                (list(codes),),
            ).fetchall()
            node_ids = {row["code"]: row["id"] for row in rows}

            unknown = codes - node_ids.keys()
            if unknown:
                raise HTTPException(
                    status_code=422,
                    detail=f"Unknown metering nodes: {sorted(unknown)}",
                )

            accepted = 0
            for m in batch.measurements:
                node_id = node_ids[m.node_code]
                measurement_id = uuid4()

                inserted = conn.execute(
                    """
                    INSERT INTO measurement (
                        id, node_id, measured_at,
                        flow_rate, pressure, temperature, source
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (node_id, measured_at) DO NOTHING
                    RETURNING id
                    """,
                    (
                        measurement_id,
                        node_id,
                        m.measured_at,
                        m.flow_rate,
                        m.pressure,
                        m.temperature,
                        m.source,
                    ),
                ).fetchone()

                if inserted is None:
                    continue

                payload = {
                    "measurement_id": str(measurement_id),
                    "node_id": str(node_id),
                    "node_code": m.node_code,
                    "measured_at": m.measured_at.isoformat(),
                    "flow_rate": m.flow_rate,
                    "pressure": m.pressure,
                    "temperature": m.temperature,
                    "source": m.source,
                }

                conn.execute(
                    """
                    INSERT INTO outbox (
                        aggregate_type, aggregate_id,
                        event_type, partition_key, payload
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        "measurement",
                        measurement_id,
                        "measurement.recorded",
                        str(node_id),
                        json.dumps(payload),
                    ),
                )
                accepted += 1

    return IntakeResult(
        accepted=accepted,
        duplicates=len(batch.measurements) - accepted,
    )