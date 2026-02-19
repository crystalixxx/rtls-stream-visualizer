from stream_handler import LS1000Parser


def test_parse_display_with_xyz():
    parser = LS1000Parser()
    event, error = parser.parse_message(
        "display:68,00A320,1614,1700000000123,2,9.65,3.27,1.50,101"
    )

    assert error is None, error
    assert event is not None
    assert event.source_type == "display"
    assert event.tag_id == "00A320"
    assert event.ts_utc_ms == 1700000000123
    assert event.layer == 2
    assert event.x == 9.65
    assert event.y == 3.27
    assert event.z == 1.5
    assert event.lng is None
    assert event.lat is None


def test_parse_status1():
    parser = LS1000Parser()
    event, error = parser.parse_message(
        "status1:58,TAG,01DD4E,1700000000001,90,3,2.4,0x03"
    )

    assert error is None, error
    assert event is not None
    assert event.source_type == "status1"
    assert event.tag_id == "01DD4E"
    assert event.ts_utc_ms == 1700000000001
    assert event.layer == 3
    assert event.status == "0x03"
    assert event.x is None
    assert event.y is None
    assert event.z is None


def test_parse_gpsposi_with_lng_lat():
    parser = LS1000Parser()
    event, error = parser.parse_message(
        "gpsposi:84,01DD4E,10481,1700000000999,4,37.6173,55.7558,165.3"
    )

    assert error is None, error
    assert event is not None
    assert event.source_type == "gpsposi"
    assert event.tag_id == "01DD4E"
    assert event.ts_utc_ms == 1700000000999
    assert event.layer == 4
    assert event.lng == 37.6173
    assert event.lat == 55.7558
    assert event.x is None
    assert event.y is None
    assert event.z == 165.3


def test_parse_json_with_local_coordinates():
    parser = LS1000Parser()
    event, error = parser.parse_message(
        '{"devid":"ABC123","timestamp":1700000000456,"position":{"x":1.2,"y":2.3,"z":3.4},"layer":1}'
    )

    assert error is None, error
    assert event is not None
    assert event.source_type == "json"
    assert event.tag_id == "ABC123"
    assert event.ts_utc_ms == 1700000000456
    assert event.x == 1.2
    assert event.y == 2.3
    assert event.z == 3.4
    assert event.layer == 1


def test_parse_json_with_lng_lat_only():
    parser = LS1000Parser()
    event, error = parser.parse_message(
        '{"tag_id":"ABC123","ts_utc_ms":1700000000456,"lng":37.6,"lat":55.7}'
    )

    assert error is None, error
    assert event is not None
    assert event.x is None
    assert event.y is None
    assert event.z is None
    assert event.lng == 37.6
    assert event.lat == 55.7


def test_unsupported_message_type_in_mvp():
    parser = LS1000Parser()
    event, error = parser.parse_message("warning:58,SOS0x01,00DD4E,1700000000001,1")

    assert event is None
    assert error is not None
    assert error.code == "unsupported_message_type"
    assert error.source_type == "warning"


def test_unknown_message_type():
    parser = LS1000Parser()
    event, error = parser.parse_message("foo:1,2,3")

    assert event is None
    assert error is not None
    assert error.code == "unknown_message_type"


def test_invalid_timestamp():
    parser = LS1000Parser()
    event, error = parser.parse_message(
        "display:68,00A320,1614,not_a_ts,2,9.65,3.27,1.50"
    )

    assert event is None
    assert error is not None
    assert error.code == "invalid_timestamp"
