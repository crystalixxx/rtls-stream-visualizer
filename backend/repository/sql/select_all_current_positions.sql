SELECT tag_id, ts_utc_ms, source_type, status, layer, area,
       x, y, z, lng, lat, origin
FROM current_positions
ORDER BY tag_id
