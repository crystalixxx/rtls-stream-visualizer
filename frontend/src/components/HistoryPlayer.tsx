import { useCallback, useState } from "react";
import type { Position } from "../types";
import type { PlaybackSpeed } from "../hooks/useHistoryPlayer";

interface Props {
  tagIds: string[];
  playing: boolean;
  speed: PlaybackSpeed;
  progress: number;
  currentTimeMs: number | null;
  timeRange: { start: number; end: number } | null;
  onPlay: () => void;
  onPause: () => void;
  onSetSpeed: (s: PlaybackSpeed) => void;
  onSeek: (progress: number) => void;
  onLoad: (points: Position[]) => void;
  onReset: () => void;
}

const SPEEDS: PlaybackSpeed[] = [1, 2, 4, 8];

function formatDatetimeLocal(ms: number): string {
  const d = new Date(ms);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function formatTime(ms: number | null): string {
  if (ms === null) return "--:--:--";
  return new Date(ms).toLocaleTimeString();
}

export function HistoryPlayer({
  tagIds,
  playing,
  speed,
  progress,
  currentTimeMs,
  timeRange,
  onPlay,
  onPause,
  onSetSpeed,
  onSeek,
  onLoad,
  onReset,
}: Props) {
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [fromTs, setFromTs] = useState("");
  const [toTs, setToTs] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleTag = useCallback((tagId: string) => {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      if (next.has(tagId)) next.delete(tagId);
      else next.add(tagId);
      return next;
    });
  }, []);

  const handleLoad = useCallback(async () => {
    if (selectedTags.size === 0) return;

    setLoading(true);
    setError(null);

    const from = fromTs ? new Date(fromTs).getTime() : null;
    const to = toTs ? new Date(toTs).getTime() : null;

    try {
      const allPoints: Position[] = [];
      for (const tagId of selectedTags) {
        const params = new URLSearchParams({ tag_id: tagId, limit: "1000" });
        if (from !== null) params.set("from_ts", String(from));
        if (to !== null) params.set("to_ts", String(to));

        const res = await fetch(`/api/v1/positions/history?${params}`);
        if (!res.ok) throw new Error(`HTTP ${res.status} for ${tagId}`);
        const body = (await res.json()) as { items: Position[] };
        allPoints.push(...body.items);
      }
      onLoad(allPoints);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [selectedTags, fromTs, toTs, onLoad]);

  const loaded = timeRange !== null;

  return (
    <div className="flex flex-col gap-2 px-3 py-2 text-sm" data-testid="history-player">
      <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
        History Player
      </div>

      <div className="max-h-32 overflow-y-auto border border-gray-200 rounded p-1">
        {tagIds.length === 0 && (
          <div className="text-xs text-gray-400 text-center py-2">
            No tags available
          </div>
        )}
        {tagIds.map((id) => (
          <label
            key={id}
            className="flex items-center gap-1.5 px-1 py-0.5 text-xs cursor-pointer hover:bg-gray-50 rounded"
          >
            <input
              type="checkbox"
              checked={selectedTags.has(id)}
              onChange={() => toggleTag(id)}
              data-testid={`history-tag-${id}`}
            />
            {id}
          </label>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          type="datetime-local"
          value={fromTs}
          onChange={(e) => setFromTs(e.target.value)}
          className="flex-1 rounded border border-gray-300 px-1.5 py-1 text-xs"
          placeholder="From"
          data-testid="history-from"
        />
        <input
          type="datetime-local"
          value={toTs}
          onChange={(e) => setToTs(e.target.value)}
          className="flex-1 rounded border border-gray-300 px-1.5 py-1 text-xs"
          placeholder="To"
          data-testid="history-to"
        />
      </div>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={handleLoad}
          disabled={selectedTags.size === 0 || loading}
          className="flex-1 rounded bg-blue-600 px-2 py-1 text-xs text-white disabled:opacity-50"
          data-testid="history-load"
        >
          {loading ? "Loading…" : "Load"}
        </button>
        <button
          type="button"
          onClick={onReset}
          className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-600"
          data-testid="history-reset"
        >
          Reset
        </button>
      </div>

      {error && (
        <div className="text-xs text-red-500" data-testid="history-error">
          {error}
        </div>
      )}

      {loaded && (
        <div className="flex flex-col gap-1.5 border-t border-gray-200 pt-2">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={playing ? onPause : onPlay}
              className="rounded bg-gray-800 px-3 py-1 text-xs text-white"
              data-testid="history-play-pause"
            >
              {playing ? "Pause" : "Play"}
            </button>
            <select
              value={speed}
              onChange={(e) =>
                onSetSpeed(Number(e.target.value) as PlaybackSpeed)
              }
              className="rounded border border-gray-300 px-1 py-1 text-xs"
              data-testid="history-speed"
            >
              {SPEEDS.map((s) => (
                <option key={s} value={s}>
                  {s}x
                </option>
              ))}
            </select>
            <span className="text-xs text-gray-500" data-testid="history-time">
              {formatTime(currentTimeMs)}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={1}
            step={0.001}
            value={progress}
            onChange={(e) => onSeek(Number(e.target.value))}
            className="w-full"
            data-testid="history-slider"
          />
          {timeRange && (
            <div className="flex justify-between text-[10px] text-gray-400">
              <span>{formatDatetimeLocal(timeRange.start)}</span>
              <span>{formatDatetimeLocal(timeRange.end)}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
