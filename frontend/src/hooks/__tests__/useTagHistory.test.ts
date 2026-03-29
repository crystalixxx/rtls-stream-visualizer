import { renderHook, waitFor } from "@testing-library/react";
import { useTagHistory } from "../useTagHistory";

const mockResponse = {
  items: [
    { tag_id: "t1", ts_utc_ms: 1000, source_type: "json", origin: "test", x: 10, y: 20, z: null, lng: null, lat: null, status: null, layer: null, area: null },
  ],
  total: 1,
};

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("useTagHistory", () => {
  it("fetches history for a given tag", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      }),
    );

    const { result } = renderHook(() => useTagHistory("t1", null, null));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toHaveLength(1);
    expect(result.current.data[0].tag_id).toBe("t1");
    expect(result.current.total).toBe(1);
    expect(result.current.error).toBeNull();
  });

  it("returns empty data when tagId is null", async () => {
    const fetchFn = vi.fn();
    vi.stubGlobal("fetch", fetchFn);

    const { result } = renderHook(() => useTagHistory(null, null, null));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual([]);
    expect(fetchFn).not.toHaveBeenCalled();
  });

  it("sets error on fetch failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.resolve({}),
      }),
    );

    const { result } = renderHook(() => useTagHistory("t1", null, null));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe("HTTP 500");
    expect(result.current.data).toEqual([]);
  });

  it("includes time range params in request", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ items: [], total: 0 }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useTagHistory("t1", 100, 200));

    await waitFor(() => expect(result.current.loading).toBe(false));

    const url = fetchMock.mock.calls[0][0] as string;
    expect(url).toContain("from_ts=100");
    expect(url).toContain("to_ts=200");
  });
});
