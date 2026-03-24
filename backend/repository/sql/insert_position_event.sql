INSERT INTO position_events (
    schema_version, event_type, origin, normalized, ingested_at_ms,
    tag_id, ts_utc_ms, source_type, status, layer, area,
    x, y, z, lng, lat, raw_message, parse_warnings
)
VALUES (
    %(schema_version)s, %(event_type)s, %(origin)s, %(normalized)s, %(ingested_at_ms)s,
    %(tag_id)s, %(ts_utc_ms)s, %(source_type)s, %(status)s, %(layer)s, %(area)s,
    %(x)s, %(y)s, %(z)s, %(lng)s, %(lat)s, %(raw_message)s, %(parse_warnings)s
)
