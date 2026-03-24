INSERT INTO current_positions (
    schema_version, event_type, origin, normalized, ingested_at_ms,
    tag_id, ts_utc_ms, source_type, status, layer, area,
    x, y, z, lng, lat, raw_message, parse_warnings
)
VALUES (
    %(schema_version)s, %(event_type)s, %(origin)s, %(normalized)s, %(ingested_at_ms)s,
    %(tag_id)s, %(ts_utc_ms)s, %(source_type)s, %(status)s, %(layer)s, %(area)s,
    %(x)s, %(y)s, %(z)s, %(lng)s, %(lat)s, %(raw_message)s, %(parse_warnings)s
)
ON CONFLICT (tag_id) DO UPDATE SET
    schema_version = EXCLUDED.schema_version,
    event_type = EXCLUDED.event_type,
    origin = EXCLUDED.origin,
    normalized = EXCLUDED.normalized,
    ingested_at_ms = EXCLUDED.ingested_at_ms,
    ts_utc_ms = EXCLUDED.ts_utc_ms,
    source_type = EXCLUDED.source_type,
    status = EXCLUDED.status,
    layer = EXCLUDED.layer,
    area = EXCLUDED.area,
    x = EXCLUDED.x,
    y = EXCLUDED.y,
    z = EXCLUDED.z,
    lng = EXCLUDED.lng,
    lat = EXCLUDED.lat,
    raw_message = EXCLUDED.raw_message,
    parse_warnings = EXCLUDED.parse_warnings
