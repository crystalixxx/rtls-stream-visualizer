from yoyo import step

__depends__ = {}


steps = [
    step(
        """
        CREATE TABLE position_events (
            id BIGSERIAL PRIMARY KEY,
            schema_version TEXT NOT NULL,
            event_type TEXT NOT NULL,
            origin TEXT NOT NULL,
            normalized BOOLEAN NOT NULL,
            ingested_at_ms BIGINT NOT NULL,
            tag_id TEXT NOT NULL,
            ts_utc_ms BIGINT NOT NULL,
            source_type TEXT NOT NULL,
            status TEXT NULL,
            layer INTEGER NULL,
            area TEXT NULL,
            x DOUBLE PRECISION NULL,
            y DOUBLE PRECISION NULL,
            z DOUBLE PRECISION NULL,
            lng DOUBLE PRECISION NULL,
            lat DOUBLE PRECISION NULL,
            raw_message TEXT NOT NULL,
            parse_warnings JSONB NOT NULL DEFAULT '[]'::jsonb
        );

        CREATE INDEX position_events_tag_id_ts_utc_ms_idx
            ON position_events (tag_id, ts_utc_ms DESC);

        CREATE INDEX position_events_ts_utc_ms_idx
            ON position_events (ts_utc_ms DESC);

        CREATE TABLE current_positions (
            tag_id TEXT PRIMARY KEY,
            schema_version TEXT NOT NULL,
            event_type TEXT NOT NULL,
            origin TEXT NOT NULL,
            normalized BOOLEAN NOT NULL,
            ingested_at_ms BIGINT NOT NULL,
            ts_utc_ms BIGINT NOT NULL,
            source_type TEXT NOT NULL,
            status TEXT NULL,
            layer INTEGER NULL,
            area TEXT NULL,
            x DOUBLE PRECISION NULL,
            y DOUBLE PRECISION NULL,
            z DOUBLE PRECISION NULL,
            lng DOUBLE PRECISION NULL,
            lat DOUBLE PRECISION NULL,
            raw_message TEXT NOT NULL,
            parse_warnings JSONB NOT NULL DEFAULT '[]'::jsonb
        );
        """,
        """
        DROP TABLE current_positions;
        DROP INDEX position_events_ts_utc_ms_idx;
        DROP INDEX position_events_tag_id_ts_utc_ms_idx;
        DROP TABLE position_events;
        """,
    )
]
