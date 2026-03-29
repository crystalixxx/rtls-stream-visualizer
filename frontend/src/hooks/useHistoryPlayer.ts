import { useCallback, useEffect, useRef, useState } from "react";
import type { Position } from "../types";

export type PlaybackSpeed = 1 | 2 | 4 | 8;

export interface UseHistoryPlayerResult {
  currentPositions: Map<string, Position>;
  playing: boolean;
  speed: PlaybackSpeed;
  progress: number;
  currentTimeMs: number | null;
  timeRange: { start: number; end: number } | null;
  play: () => void;
  pause: () => void;
  setSpeed: (s: PlaybackSpeed) => void;
  seek: (progress: number) => void;
  load: (points: Position[]) => void;
  reset: () => void;
}

export function useHistoryPlayer(): UseHistoryPlayerResult {
  const [sortedPoints, setSortedPoints] = useState<Position[]>([]);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeedState] = useState<PlaybackSpeed>(1);
  const [currentTimeMs, setCurrentTimeMs] = useState<number | null>(null);

  const playingRef = useRef(false);
  const speedRef = useRef<PlaybackSpeed>(1);
  const lastFrameRef = useRef<number | null>(null);
  const currentTimeMsRef = useRef<number | null>(null);
  const sortedPointsRef = useRef<Position[]>([]);
  const rafRef = useRef<number | null>(null);

  const timeRange =
    sortedPoints.length > 0
      ? {
          start: sortedPoints[0].ts_utc_ms,
          end: sortedPoints[sortedPoints.length - 1].ts_utc_ms,
        }
      : null;

  const duration = timeRange ? timeRange.end - timeRange.start : 0;

  const progress =
    timeRange && currentTimeMs !== null && duration > 0
      ? Math.min(
          1,
          Math.max(0, (currentTimeMs - timeRange.start) / duration),
        )
      : 0;

  const computePositions = useCallback(
    (atMs: number): Map<string, Position> => {
      const map = new Map<string, Position>();
      for (const p of sortedPointsRef.current) {
        if (p.ts_utc_ms > atMs) break;
        map.set(p.tag_id, p);
      }
      return map;
    },
    [],
  );

  const [currentPositions, setCurrentPositions] = useState<
    Map<string, Position>
  >(() => new Map());

  const tick = useCallback((timestamp: number) => {
    if (!playingRef.current) return;

    const pts = sortedPointsRef.current;
    if (pts.length === 0) return;

    const start = pts[0].ts_utc_ms;
    const end = pts[pts.length - 1].ts_utc_ms;

    if (lastFrameRef.current !== null) {
      const realDelta = timestamp - lastFrameRef.current;
      const simDelta = realDelta * speedRef.current;
      const prev = currentTimeMsRef.current ?? start;
      const next = Math.min(prev + simDelta, end);
      currentTimeMsRef.current = next;
      setCurrentTimeMs(next);
      setCurrentPositions(computePositions(next));

      if (next >= end) {
        playingRef.current = false;
        setPlaying(false);
        lastFrameRef.current = null;
        return;
      }
    }

    lastFrameRef.current = timestamp;
    rafRef.current = requestAnimationFrame(tick);
  }, [computePositions]);

  const play = useCallback(() => {
    if (sortedPointsRef.current.length === 0) return;
    const pts = sortedPointsRef.current;
    const end = pts[pts.length - 1].ts_utc_ms;

    if (currentTimeMsRef.current !== null && currentTimeMsRef.current >= end) {
      currentTimeMsRef.current = pts[0].ts_utc_ms;
      setCurrentTimeMs(pts[0].ts_utc_ms);
      setCurrentPositions(new Map());
    }

    playingRef.current = true;
    lastFrameRef.current = null;
    setPlaying(true);
    rafRef.current = requestAnimationFrame(tick);
  }, [tick]);

  const pause = useCallback(() => {
    playingRef.current = false;
    setPlaying(false);
    lastFrameRef.current = null;
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const setSpeed = useCallback((s: PlaybackSpeed) => {
    speedRef.current = s;
    setSpeedState(s);
  }, []);

  const seek = useCallback(
    (p: number) => {
      if (sortedPointsRef.current.length === 0) return;
      const pts = sortedPointsRef.current;
      const start = pts[0].ts_utc_ms;
      const end = pts[pts.length - 1].ts_utc_ms;
      const t = start + (end - start) * Math.max(0, Math.min(1, p));
      currentTimeMsRef.current = t;
      setCurrentTimeMs(t);
      setCurrentPositions(computePositions(t));
    },
    [computePositions],
  );

  const load = useCallback((points: Position[]) => {
    const sorted = [...points].sort((a, b) => a.ts_utc_ms - b.ts_utc_ms);
    sortedPointsRef.current = sorted;
    setSortedPoints(sorted);

    if (sorted.length > 0) {
      const start = sorted[0].ts_utc_ms;
      currentTimeMsRef.current = start;
      setCurrentTimeMs(start);
      setCurrentPositions(new Map());
    } else {
      currentTimeMsRef.current = null;
      setCurrentTimeMs(null);
      setCurrentPositions(new Map());
    }

    playingRef.current = false;
    setPlaying(false);
    lastFrameRef.current = null;
  }, []);

  const reset = useCallback(() => {
    pause();
    sortedPointsRef.current = [];
    setSortedPoints([]);
    currentTimeMsRef.current = null;
    setCurrentTimeMs(null);
    setCurrentPositions(new Map());
  }, [pause]);

  useEffect(() => {
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return {
    currentPositions,
    playing,
    speed,
    progress,
    currentTimeMs,
    timeRange,
    play,
    pause,
    setSpeed,
    seek,
    load,
    reset,
  };
}
