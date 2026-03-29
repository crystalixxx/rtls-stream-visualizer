SELECT tag_id, ts_utc_ms, source_type, status, layer, area,
       x, y, z, lng, lat, origin
FROM position_events
WHERE tag_id = %(tag_id)s
  AND (%(from_ts)s IS NULL OR ts_utc_ms >= %(from_ts)s)
  AND (%(to_ts)s IS NULL OR ts_utc_ms <= %(to_ts)s)
ORDER BY ts_utc_ms DESC
LIMIT %(limit)s OFFSET %(offset)s
