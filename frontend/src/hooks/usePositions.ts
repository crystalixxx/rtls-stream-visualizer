import { useCallback, useEffect, useRef, useState } from "react";
import type { Position, WsState } from "../types";

const MAX_BACKOFF_MS = 30_000;
const BASE_BACKOFF_MS = 1_000;
const EPS_WINDOW_MS = 1_000;

function wsUrl(): string {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/api/v1/ws/positions`;
}

function positionFromSnapshot(item: Position): Position {
  return item;
}

function positionFromEnvelope(envelope: Record<string, unknown>): Position {
  const payload = envelope.payload as Position | undefined;
  if (payload && typeof payload.tag_id === "string") {
    return payload;
  }
  return envelope as unknown as Position;
}

export interface UsePositionsResult {
  positions: Map<string, Position>;
  connectionState: WsState;
  eventsPerSec: number;
  lastEventTs: number | null;
}

export function usePositions(): UsePositionsResult {
  const [positions, setPositions] = useState<Map<string, Position>>(
    () => new Map(),
  );
  const [connectionState, setConnectionState] =
    useState<WsState>("disconnected");
  const [eventsPerSec, setEventsPerSec] = useState(0);
  const [lastEventTs, setLastEventTs] = useState<number | null>(null);

  const retriesRef = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);
  const mountedRef = useRef(true);
  const gotSnapshotRef = useRef(false);
  const eventTimestampsRef = useRef<number[]>([]);
  const epsIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const updateEps = useCallback(() => {
    const now = Date.now();
    const cutoff = now - EPS_WINDOW_MS;
    const ts = eventTimestampsRef.current;
    const firstValid = ts.findIndex((t) => t >= cutoff);
    if (firstValid > 0) {
      eventTimestampsRef.current = ts.slice(firstValid);
    } else if (firstValid === -1) {
      eventTimestampsRef.current = [];
    }
    setEventsPerSec(eventTimestampsRef.current.length);
  }, []);

  const recordEvent = useCallback(
    (eventTsMs: number) => {
      eventTimestampsRef.current.push(Date.now());
      setLastEventTs(eventTsMs);
    },
    [],
  );

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    const isReconnect = retriesRef.current > 0;
    setConnectionState(isReconnect ? "reconnecting" : "connecting");
    gotSnapshotRef.current = false;

    const ws = new WebSocket(wsUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      retriesRef.current = 0;
      setConnectionState("connected");
    };

    ws.onmessage = (event: MessageEvent) => {
      if (!mountedRef.current) return;

      const data: unknown = JSON.parse(event.data as string);

      if (!gotSnapshotRef.current && Array.isArray(data)) {
        gotSnapshotRef.current = true;
        const map = new Map<string, Position>();
        for (const item of data as Position[]) {
          const pos = positionFromSnapshot(item);
          map.set(pos.tag_id, pos);
        }
        setPositions(map);
        return;
      }

      const envelope = data as Record<string, unknown>;
      const pos = positionFromEnvelope(envelope);
      recordEvent(pos.ts_utc_ms);
      setPositions((prev) => {
        const next = new Map(prev);
        next.set(pos.tag_id, pos);
        return next;
      });
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setConnectionState("disconnected");
      scheduleReconnect();
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [recordEvent]);

  const scheduleReconnect = useCallback(() => {
    if (!mountedRef.current) return;
    const delay = Math.min(
      BASE_BACKOFF_MS * 2 ** retriesRef.current,
      MAX_BACKOFF_MS,
    );
    retriesRef.current += 1;
    setTimeout(() => {
      if (mountedRef.current) connect();
    }, delay);
  }, [connect]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    epsIntervalRef.current = setInterval(updateEps, 500);

    return () => {
      mountedRef.current = false;
      wsRef.current?.close();
      if (epsIntervalRef.current) clearInterval(epsIntervalRef.current);
    };
  }, [connect, updateEps]);

  return { positions, connectionState, eventsPerSec, lastEventTs };
}
