import time
from typing import Optional

from stream_handler.ls1000_parser import NormalizedEvent


class JsonStreamNormalizer:
    def __init__(self, origin: str):
        self.origin = origin

    def normalize(self, obj: dict, raw_message: str) -> Optional[NormalizedEvent]:
        tag_id = self._first_str(obj, "tag_id", "devid", "dev_id", "tag", "id")
        if tag_id is None:
            return None

        warnings: list[str] = []
        ts = self._first_int(obj, "ts_utc_ms", "timestamp", "ts")
        if ts is None:
            ts = int(time.time() * 1000)
            warnings.append("timestamp_missing_used_ingestion_time")

        x, y, z = self._extract_xyz(obj)
        lng = self._first_float(obj, "lng", "lon", "longitude")
        lat = self._first_float(obj, "lat", "latitude")
        layer = self._first_int(obj, "layer", "layid", "floor")
        area = self._first_str(obj, "area", "rgn")
        status = self._first_str(obj, "status")

        return NormalizedEvent(
            origin=self.origin,
            tag_id=tag_id,
            ts_utc_ms=ts,
            x=x,
            y=y,
            z=z,
            layer=layer,
            area=area,
            status=status,
            source_type="json",
            raw_message=raw_message,
            lng=lng,
            lat=lat,
            parse_warnings=warnings,
        )

    def _extract_xyz(
        self, obj: dict
    ) -> tuple[Optional[float], Optional[float], Optional[float]]:
        position = obj.get("position")
        if isinstance(position, dict):
            x = self._first_float(position, "x")
            y = self._first_float(position, "y")
            z = self._first_float(position, "z")
            if x is not None or y is not None or z is not None:
                return x, y, z
        return (
            self._first_float(obj, "x"),
            self._first_float(obj, "y"),
            self._first_float(obj, "z"),
        )

    @staticmethod
    def _first_str(obj: dict, *keys: str) -> Optional[str]:
        for key in keys:
            value = obj.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return None

    @staticmethod
    def _first_int(obj: dict, *keys: str) -> Optional[int]:
        for key in keys:
            value = obj.get(key)
            parsed = JsonStreamNormalizer._parse_int(value)
            if parsed is not None:
                return parsed
        return None

    @staticmethod
    def _first_float(obj: dict, *keys: str) -> Optional[float]:
        for key in keys:
            value = obj.get(key)
            parsed = JsonStreamNormalizer._parse_float(value)
            if parsed is not None:
                return parsed
        return None

    @staticmethod
    def _parse_int(value) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            try:
                return int(text)
            except ValueError:
                return None
        return None

    @staticmethod
    def _parse_float(value) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            try:
                return float(text)
            except ValueError:
                return None
        return None
