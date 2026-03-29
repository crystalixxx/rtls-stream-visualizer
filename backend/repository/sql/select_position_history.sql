SELECT tag_id, ts_utc_ms, source_type, status, layer, area,
       x, y, z, lng, lat, origin
FROM position_events
WHERE tag_id = %(tag_id)s
ORDER BY ts_utc_ms DESC
LIMIT %(limit)s OFFSET %(offset)s
