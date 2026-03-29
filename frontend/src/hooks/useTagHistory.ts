import { useCallback, useEffect, useState } from "react";
import type { Position } from "../types";

interface HistoryResponse {
  items: Position[];
  total: number;
}

interface UseTagHistoryResult {
  data: Position[];
  total: number;
  loading: boolean;
  error: string | null;
}

export function useTagHistory(
  tagId: string | null,
  fromTs: number | null,
  toTs: number | null,
): UseTagHistoryResult {
  const [data, setData] = useState<Position[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = useCallback(async () => {
    if (!tagId) {
      setData([]);
      setTotal(0);
      return;
    }

    setLoading(true);
    setError(null);

    const params = new URLSearchParams({ tag_id: tagId });
    if (fromTs !== null) params.set("from_ts", String(fromTs));
    if (toTs !== null) params.set("to_ts", String(toTs));
    params.set("limit", "1000");

    try {
      const res = await fetch(`/api/v1/positions/history?${params}`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const body = (await res.json()) as HistoryResponse;
      setData(body.items);
      setTotal(body.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setData([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [tagId, fromTs, toTs]);

  useEffect(() => {
    void fetchHistory();
  }, [fetchHistory]);

  return { data, total, loading, error };
}
