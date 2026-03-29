import { renderHook, act } from "@testing-library/react";
import { useHistoryPlayer } from "../useHistoryPlayer";
import type { Position } from "../../types";

function makePos(tag_id: string, ts: number): Position {
  return {
    tag_id,
    ts_utc_ms: ts,
    source_type: "json",
    origin: "test",
    status: null,
    layer: null,
    area: null,
    x: ts * 0.1,
    y: ts * 0.2,
    z: null,
    lng: null,
    lat: null,
  };
}

describe("useHistoryPlayer", () => {
  it("starts with empty state", () => {
    const { result } = renderHook(() => useHistoryPlayer());

    expect(result.current.currentPositions.size).toBe(0);
    expect(result.current.playing).toBe(false);
    expect(result.current.progress).toBe(0);
    expect(result.current.currentTimeMs).toBeNull();
    expect(result.current.timeRange).toBeNull();
  });

  it("loads points and sets time range", () => {
    const { result } = renderHook(() => useHistoryPlayer());

    const points = [makePos("t1", 1000), makePos("t1", 2000), makePos("t1", 3000)];

    act(() => {
      result.current.load(points);
    });

    expect(result.current.timeRange).toEqual({ start: 1000, end: 3000 });
    expect(result.current.currentTimeMs).toBe(1000);
    expect(result.current.progress).toBe(0);
  });

  it("seek updates progress and positions", () => {
    const { result } = renderHook(() => useHistoryPlayer());

    const points = [
      makePos("t1", 1000),
      makePos("t1", 2000),
      makePos("t1", 3000),
    ];

    act(() => result.current.load(points));

    act(() => result.current.seek(0.5));

    expect(result.current.currentTimeMs).toBe(2000);
    expect(result.current.currentPositions.size).toBe(1);
    expect(result.current.currentPositions.get("t1")?.ts_utc_ms).toBe(2000);
  });

  it("seek to end includes all points", () => {
    const { result } = renderHook(() => useHistoryPlayer());

    const points = [
      makePos("t1", 1000),
      makePos("t2", 2000),
    ];

    act(() => result.current.load(points));
    act(() => result.current.seek(1));

    expect(result.current.currentPositions.size).toBe(2);
  });

  it("setSpeed updates speed", () => {
    const { result } = renderHook(() => useHistoryPlayer());

    act(() => result.current.setSpeed(4));

    expect(result.current.speed).toBe(4);
  });

  it("reset clears everything", () => {
    const { result } = renderHook(() => useHistoryPlayer());

    act(() => result.current.load([makePos("t1", 1000)]));
    act(() => result.current.reset());

    expect(result.current.currentPositions.size).toBe(0);
    expect(result.current.timeRange).toBeNull();
    expect(result.current.currentTimeMs).toBeNull();
    expect(result.current.playing).toBe(false);
  });

  it("merges multiple tags correctly on seek", () => {
    const { result } = renderHook(() => useHistoryPlayer());

    const points = [
      makePos("t1", 1000),
      makePos("t2", 1500),
      makePos("t1", 2000),
      makePos("t2", 2500),
    ];

    act(() => result.current.load(points));
    act(() => result.current.seek(0.5));

    const positions = result.current.currentPositions;
    expect(positions.size).toBe(2);
    expect(positions.get("t1")?.ts_utc_ms).toBe(1000);
    expect(positions.get("t2")?.ts_utc_ms).toBe(1500);
  });
});
