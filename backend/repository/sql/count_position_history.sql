SELECT COUNT(*)
FROM position_events
WHERE tag_id = %(tag_id)s
  AND (%(from_ts)s IS NULL OR ts_utc_ms >= %(from_ts)s)
  AND (%(to_ts)s IS NULL OR ts_utc_ms <= %(to_ts)s)
