from pydantic import BaseModel


class PositionOut(BaseModel):
    tag_id: str
    ts_utc_ms: int
    source_type: str
    origin: str
    status: str | None = None
    layer: int | None = None
    area: str | None = None
    x: float | None = None
    y: float | None = None
    z: float | None = None
    lng: float | None = None
    lat: float | None = None


class PositionHistoryResponse(BaseModel):
    items: list[PositionOut]
    total: int
