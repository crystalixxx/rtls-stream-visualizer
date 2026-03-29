import { renderHook, act } from "@testing-library/react";
import { usePositions } from "../usePositions";

type WsHandler = {
  onopen: (() => void) | null;
  onmessage: ((e: { data: string }) => void) | null;
  onclose: (() => void) | null;
  onerror: (() => void) | null;
  close: ReturnType<typeof vi.fn>;
  readyState: number;
};

let wsInstances: WsHandler[];

beforeEach(() => {
  wsInstances = [];
  vi.useFakeTimers();

  class MockWebSocket {
    onopen: (() => void) | null = null;
    onmessage: ((e: { data: string }) => void) | null = null;
    onclose: (() => void) | null = null;
    onerror: (() => void) | null = null;
    close = vi.fn(() => {
      this.onclose?.();
    });
    readyState = 0;

    constructor(_url: string) {
      wsInstances.push(this);
    }
  }

  vi.stubGlobal("WebSocket", MockWebSocket);
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

function lastWs(): WsHandler {
  return wsInstances[wsInstances.length - 1]!;
}

describe("usePositions", () => {
  it("connects and sets state to connected on open", () => {
    const { result } = renderHook(() => usePositions());

    expect(result.current.connectionState).toBe("connecting");

    act(() => {
      lastWs().onopen?.();
    });

    expect(result.current.connectionState).toBe("connected");
  });

  it("populates positions from snapshot (first message as array)", () => {
    const { result } = renderHook(() => usePositions());

    act(() => lastWs().onopen?.());

    const snapshot = [
      { tag_id: "t1", ts_utc_ms: 1000, source_type: "json", origin: "test", x: 10, y: 20, z: null, lng: null, lat: null, status: null, layer: null, area: null },
      { tag_id: "t2", ts_utc_ms: 2000, source_type: "json", origin: "test", x: 30, y: 40, z: null, lng: null, lat: null, status: null, layer: null, area: null },
    ];

    act(() => {
      lastWs().onmessage?.({ data: JSON.stringify(snapshot) });
    });

    expect(result.current.positions.size).toBe(2);
    expect(result.current.positions.get("t1")?.x).toBe(10);
    expect(result.current.positions.get("t2")?.y).toBe(40);
  });

  it("upserts position from live envelope update", () => {
    const { result } = renderHook(() => usePositions());

    act(() => lastWs().onopen?.());
    act(() => {
      lastWs().onmessage?.({ data: JSON.stringify([]) });
    });

    const envelope = {
      payload: { tag_id: "t-live", ts_utc_ms: 5000, source_type: "display", origin: "ls-1000", x: 1, y: 2, z: null, lng: null, lat: null, status: null, layer: null, area: null },
    };

    act(() => {
      lastWs().onmessage?.({ data: JSON.stringify(envelope) });
    });

    expect(result.current.positions.size).toBe(1);
    expect(result.current.positions.get("t-live")?.ts_utc_ms).toBe(5000);
  });

  it("schedules reconnect on close with backoff", () => {
    const { result } = renderHook(() => usePositions());

    act(() => lastWs().onopen?.());

    expect(wsInstances).toHaveLength(1);

    act(() => {
      lastWs().onclose?.();
    });

    expect(result.current.connectionState).toBe("disconnected");

    act(() => {
      vi.advanceTimersByTime(1_000);
    });

    expect(wsInstances).toHaveLength(2);
  });

  it("closes socket on unmount", () => {
    const { unmount } = renderHook(() => usePositions());
    const ws = lastWs();

    unmount();

    expect(ws.close).toHaveBeenCalled();
  });

  it("tracks eventsPerSec for live updates", () => {
    const { result } = renderHook(() => usePositions());

    act(() => lastWs().onopen?.());
    act(() => {
      lastWs().onmessage?.({ data: JSON.stringify([]) });
    });

    const envelope = {
      payload: { tag_id: "t1", ts_utc_ms: 5000, source_type: "display", origin: "ls-1000", x: 1, y: 2, z: null, lng: null, lat: null, status: null, layer: null, area: null },
    };

    act(() => {
      lastWs().onmessage?.({ data: JSON.stringify(envelope) });
    });

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(result.current.eventsPerSec).toBe(1);
  });

  it("tracks lastEventTs from live updates", () => {
    const { result } = renderHook(() => usePositions());

    expect(result.current.lastEventTs).toBeNull();

    act(() => lastWs().onopen?.());
    act(() => {
      lastWs().onmessage?.({ data: JSON.stringify([]) });
    });

    const envelope = {
      payload: { tag_id: "t1", ts_utc_ms: 9999, source_type: "display", origin: "ls-1000", x: 1, y: 2, z: null, lng: null, lat: null, status: null, layer: null, area: null },
    };

    act(() => {
      lastWs().onmessage?.({ data: JSON.stringify(envelope) });
    });

    expect(result.current.lastEventTs).toBe(9999);
  });
});
