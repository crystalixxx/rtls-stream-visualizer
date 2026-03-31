import time
from unittest.mock import patch

import pytest

from stream_handler.json_normalizer import JsonStreamNormalizer


@pytest.fixture()
def normalizer() -> JsonStreamNormalizer:
    return JsonStreamNormalizer(origin="test")


class TestNormalize:
    def test_basic_flat_object(self, normalizer: JsonStreamNormalizer):
        obj = {"tag_id": "t1", "x": 1.0, "y": 2.0, "z": 3.0, "ts_utc_ms": 5000}
        result = normalizer.normalize(obj, raw_message='{"tag_id":"t1"}')

        assert result is not None
        assert result.tag_id == "t1"
        assert result.x == 1.0
        assert result.y == 2.0
        assert result.z == 3.0
        assert result.ts_utc_ms == 5000
        assert result.origin == "test"
        assert result.source_type == "json"

    def test_nested_position(self, normalizer: JsonStreamNormalizer):
        obj = {
            "tag_id": "t2",
            "position": {"x": 10.0, "y": 20.0, "z": 30.0},
            "ts_utc_ms": 6000,
        }
        result = normalizer.normalize(obj, raw_message="{}")

        assert result is not None
        assert result.x == 10.0
        assert result.y == 20.0
        assert result.z == 30.0

    def test_missing_tag_id_returns_none(self, normalizer: JsonStreamNormalizer):
        obj = {"x": 1.0, "y": 2.0}
        assert normalizer.normalize(obj, raw_message="{}") is None

    def test_alternative_tag_keys(self, normalizer: JsonStreamNormalizer):
        for key in ("devid", "dev_id", "tag", "id"):
            obj = {key: "tag-alt", "ts_utc_ms": 1000}
            result = normalizer.normalize(obj, raw_message="{}")
            assert result is not None
            assert result.tag_id == "tag-alt"

    def test_missing_timestamp_uses_ingestion_time(
        self, normalizer: JsonStreamNormalizer
    ):
        fake_now_ms = 9999000
        with patch.object(time, "time", return_value=fake_now_ms / 1000):
            result = normalizer.normalize({"tag_id": "t3"}, raw_message="{}")

        assert result is not None
        assert result.ts_utc_ms == fake_now_ms
        assert "timestamp_missing_used_ingestion_time" in result.parse_warnings

    def test_geo_coordinates(self, normalizer: JsonStreamNormalizer):
        obj = {"tag_id": "g1", "lng": 37.6, "lat": 55.7, "ts_utc_ms": 1000}
        result = normalizer.normalize(obj, raw_message="{}")

        assert result is not None
        assert result.lng == 37.6
        assert result.lat == 55.7

    def test_layer_and_area(self, normalizer: JsonStreamNormalizer):
        obj = {"tag_id": "t4", "layer": 2, "area": "zone-a", "ts_utc_ms": 1000}
        result = normalizer.normalize(obj, raw_message="{}")

        assert result is not None
        assert result.layer == 2
        assert result.area == "zone-a"

    def test_status_field(self, normalizer: JsonStreamNormalizer):
        obj = {"tag_id": "t5", "status": "active", "ts_utc_ms": 1000}
        result = normalizer.normalize(obj, raw_message="{}")

        assert result is not None
        assert result.status == "active"


class TestHelperMethods:
    def test_first_str_returns_first_non_empty(self):
        obj = {"a": "", "b": "hello"}
        assert JsonStreamNormalizer._first_str(obj, "a", "b") == "hello"

    def test_first_str_returns_none_when_all_empty(self):
        assert JsonStreamNormalizer._first_str({}, "a", "b") is None

    def test_first_int_parses_string(self):
        assert JsonStreamNormalizer._first_int({"v": "42"}, "v") == 42

    def test_first_int_returns_none_for_invalid(self):
        assert JsonStreamNormalizer._first_int({"v": "abc"}, "v") is None

    def test_first_float_from_int(self):
        assert JsonStreamNormalizer._first_float({"v": 5}, "v") == 5.0

    def test_first_float_from_string(self):
        assert JsonStreamNormalizer._first_float({"v": "3.14"}, "v") == pytest.approx(
            3.14
        )

    def test_first_float_returns_none_for_empty_string(self):
        assert JsonStreamNormalizer._first_float({"v": ""}, "v") is None

    def test_extract_xyz_prefers_nested_position(self):
        n = JsonStreamNormalizer(origin="test")
        obj = {"x": 100.0, "position": {"x": 1.0, "y": 2.0}}
        x, y, z = n._extract_xyz(obj)
        assert x == 1.0
        assert y == 2.0
        assert z is None

    def test_extract_xyz_falls_back_to_top_level(self):
        n = JsonStreamNormalizer(origin="test")
        obj = {"x": 10.0, "y": 20.0, "z": 30.0}
        x, y, z = n._extract_xyz(obj)
        assert (x, y, z) == (10.0, 20.0, 30.0)
