import json
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NormalizedEvent:
    origin: str
    tag_id: str
    ts_utc_ms: int
    x: Optional[float]
    y: Optional[float]
    z: Optional[float]
    layer: Optional[int]
    area: Optional[str]
    status: Optional[str]
    source_type: str
    raw_message: str
    lng: Optional[float] = None
    lat: Optional[float] = None
    parse_warnings: list[str] = field(default_factory=list)


@dataclass
class ParseError:
    code: str
    message: str
    raw_message: str
    source_type: str = "unknown"


class LS1000Parser:
    _BASE_TYPES = {"display", "status1", "status2", "gpsposi"}
    _UNSUPPORTED_TYPES = {"warning", "summary", "rawdata"}
    _COORD_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")

    def parse_message(
        self, raw_message: str
    ) -> tuple[Optional[NormalizedEvent], Optional[ParseError]]:
        raw = raw_message.strip()
        if not raw:
            return None, ParseError(
                code="empty_message",
                message="Message is empty",
                raw_message=raw_message,
            )

        if raw.startswith("{"):
            return self._parse_json(raw_message, raw)

        if ":" not in raw:
            return None, ParseError(
                code="invalid_format",
                message="Expected '<type>:<payload>' format",
                raw_message=raw_message,
            )

        type_name, payload = raw.split(":", 1)
        source_type = type_name.strip().lower()
        if source_type in self._UNSUPPORTED_TYPES:
            return None, ParseError(
                code="unsupported_message_type",
                message=f"Message type '{source_type}' is not included in MVP",
                raw_message=raw_message,
                source_type=source_type,
            )

        if source_type not in self._BASE_TYPES:
            return None, ParseError(
                code="unknown_message_type",
                message=f"Unknown message type '{source_type}'",
                raw_message=raw_message,
                source_type=source_type,
            )

        tokens = [part.strip() for part in payload.split(",") if part.strip()]
        if not tokens:
            return None, ParseError(
                code="invalid_payload",
                message="Payload is empty",
                raw_message=raw_message,
                source_type=source_type,
            )

        if source_type == "display":
            return self._parse_display(raw_message, tokens)
        if source_type == "status1":
            return self._parse_status1(raw_message, tokens)
        if source_type == "status2":
            return self._parse_status2(raw_message, tokens)
        return self._parse_gpsposi(raw_message, tokens)

    def _parse_json(
        self, raw_message: str, raw: str
    ) -> tuple[Optional[NormalizedEvent], Optional[ParseError]]:
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            return None, ParseError(
                code="invalid_json",
                message=f"Invalid JSON: {exc}",
                raw_message=raw_message,
                source_type="json",
            )

        tag_id = self._first_str(obj, "tag_id", "devid", "dev_id", "tag", "id")
        if tag_id is None:
            return None, ParseError(
                code="missing_field",
                message="Missing tag id in JSON payload",
                raw_message=raw_message,
                source_type="json",
            )

        ts = self._first_int(obj, "ts_utc_ms", "timestamp", "ts")
        if ts is None:
            return None, ParseError(
                code="missing_field",
                message="Missing timestamp in JSON payload",
                raw_message=raw_message,
                source_type="json",
            )

        x, y, z = self._extract_xyz_from_json(obj)
        lng = self._first_float(obj, "lng", "lon", "longitude")
        lat = self._first_float(obj, "lat", "latitude")
        layer = self._first_int(obj, "layer", "layid", "floor")
        status = self._first_str(obj, "status")
        area = self._first_str(obj, "area")

        return (
            NormalizedEvent(
                origin="ls-1000",
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
            ),
            None,
        )

    def _parse_display(
        self, raw_message: str, tokens: list[str]
    ) -> tuple[Optional[NormalizedEvent], Optional[ParseError]]:
        # Expected shape: [LEN],[DEVID],[SEQ],[TIMESTAMP],[LAYID],...
        if len(tokens) < 5:
            return self._err(
                raw_message,
                "display",
                "invalid_payload",
                "display requires at least 5 fields",
            )

        tag_id = tokens[1]
        ts = self._parse_int(tokens[3])
        if ts is None:
            return self._err(
                raw_message, "display", "invalid_timestamp", "Invalid TIMESTAMP field"
            )

        layer = self._parse_int(tokens[4])
        x, y, z = self._extract_xyz_from_tokens(tokens, start=5)

        return (
            NormalizedEvent(
                origin="ls-1000",
                tag_id=tag_id,
                ts_utc_ms=ts,
                x=x,
                y=y,
                z=z,
                layer=layer,
                area=self._safe_token(tokens, 6) if x is None else None,
                status=None,
                source_type="display",
                raw_message=raw_message,
            ),
            None,
        )

    def _parse_status1(
        self, raw_message: str, tokens: list[str]
    ) -> tuple[Optional[NormalizedEvent], Optional[ParseError]]:
        # Expected shape: [LEN],TAG,[DEVID],[TIMESTAMP],[VBAT],[LAYID],[VELO],[SOS]
        if len(tokens) < 6:
            return self._err(
                raw_message,
                "status1",
                "invalid_payload",
                "status1 requires at least 6 fields",
            )

        tag_id = tokens[2]
        ts = self._parse_int(tokens[3])
        if ts is None:
            return self._err(
                raw_message, "status1", "invalid_timestamp", "Invalid TIMESTAMP field"
            )

        layer = self._parse_int(tokens[5])
        status = self._safe_token(tokens, 7)

        return (
            NormalizedEvent(
                origin="ls-1000",
                tag_id=tag_id,
                ts_utc_ms=ts,
                x=None,
                y=None,
                z=None,
                layer=layer,
                area=None,
                status=status,
                source_type="status1",
                raw_message=raw_message,
            ),
            None,
        )

    def _parse_status2(
        self, raw_message: str, tokens: list[str]
    ) -> tuple[Optional[NormalizedEvent], Optional[ParseError]]:
        # Common shape in protocol examples: [LEN],[DEVID],[SEQ],[TIMESTAMP],...
        if len(tokens) < 4:
            return self._err(
                raw_message,
                "status2",
                "invalid_payload",
                "status2 requires at least 4 fields",
            )

        tag_id = tokens[1]
        ts = self._parse_int(tokens[3])
        if ts is None:
            return self._err(
                raw_message, "status2", "invalid_timestamp", "Invalid TIMESTAMP field"
            )

        layer = self._parse_int(tokens[4]) if len(tokens) > 4 else None
        return (
            NormalizedEvent(
                origin="ls-1000",
                tag_id=tag_id,
                ts_utc_ms=ts,
                x=None,
                y=None,
                z=None,
                layer=layer,
                area=None,
                status=None,
                source_type="status2",
                raw_message=raw_message,
            ),
            None,
        )

    def _parse_gpsposi(
        self, raw_message: str, tokens: list[str]
    ) -> tuple[Optional[NormalizedEvent], Optional[ParseError]]:
        # Expected shape: [LEN],[DEVID],[SEQ],[TIMESTAMP],[LAYID],[LNG],[LAT],[z]
        if len(tokens) < 7:
            return self._err(
                raw_message,
                "gpsposi",
                "invalid_payload",
                "gpsposi requires at least 7 fields",
            )

        tag_id = tokens[1]
        ts = self._parse_int(tokens[3])
        if ts is None:
            return self._err(
                raw_message, "gpsposi", "invalid_timestamp", "Invalid TIMESTAMP field"
            )

        layer = self._parse_int(tokens[4])
        lng = self._parse_float(tokens[5])
        lat = self._parse_float(tokens[6])
        z = self._parse_float(tokens[7]) if len(tokens) > 7 else None

        if lng is None or lat is None:
            return self._err(
                raw_message, "gpsposi", "invalid_coordinates", "Invalid lng/lat values"
            )

        return (
            NormalizedEvent(
                origin="ls-1000",
                tag_id=tag_id,
                ts_utc_ms=ts,
                x=None,
                y=None,
                z=z,
                layer=layer,
                area=None,
                status=None,
                source_type="gpsposi",
                raw_message=raw_message,
                lng=lng,
                lat=lat,
            ),
            None,
        )

    def _extract_xyz_from_tokens(
        self, tokens: list[str], start: int
    ) -> tuple[Optional[float], Optional[float], Optional[float]]:
        if len(tokens) >= start + 3:
            x = self._parse_float(tokens[start])
            y = self._parse_float(tokens[start + 1])
            z = self._parse_float(tokens[start + 2])
            if x is not None and y is not None and z is not None:
                return x, y, z

        if len(tokens) > start:
            candidates = self._COORD_RE.findall(tokens[start])
            if len(candidates) >= 3:
                return float(candidates[0]), float(candidates[1]), float(candidates[2])

        return None, None, None

    def _extract_xyz_from_json(
        self, obj: dict
    ) -> tuple[Optional[float], Optional[float], Optional[float]]:
        position = obj.get("position")
        if isinstance(position, dict):
            x = self._parse_float(position.get("x"))
            y = self._parse_float(position.get("y"))
            z = self._parse_float(position.get("z"))
            if x is not None and y is not None:
                return x, y, z

        x = self._first_float(obj, "x")
        y = self._first_float(obj, "y")
        z = self._first_float(obj, "z")
        return x, y, z

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
                if text.lower().startswith("0x"):
                    return int(text, 16)
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

    def _first_int(self, obj: dict, *keys: str) -> Optional[int]:
        for key in keys:
            if key in obj:
                value = self._parse_int(obj.get(key))
                if value is not None:
                    return value
        return None

    def _first_float(self, obj: dict, *keys: str) -> Optional[float]:
        for key in keys:
            if key in obj:
                value = self._parse_float(obj.get(key))
                if value is not None:
                    return value
        return None

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
    def _safe_token(tokens: list[str], index: int) -> Optional[str]:
        if index >= len(tokens):
            return None
        token = tokens[index].strip()
        return token or None

    @staticmethod
    def _err(
        raw_message: str, source_type: str, code: str, message: str
    ) -> tuple[None, ParseError]:
        return None, ParseError(
            code=code,
            message=message,
            raw_message=raw_message,
            source_type=source_type,
        )
