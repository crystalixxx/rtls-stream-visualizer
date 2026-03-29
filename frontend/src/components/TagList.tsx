import type { Position } from "../types";

interface Props {
  positions: Map<string, Position>;
  selectedTagId: string | null;
  onSelectTag: (tagId: string) => void;
}

function formatTime(ms: number): string {
  return new Date(ms).toLocaleTimeString();
}

export function TagList({ positions, selectedTagId, onSelectTag }: Props) {
  const sorted = Array.from(positions.values()).sort((a, b) =>
    a.tag_id.localeCompare(b.tag_id),
  );

  return (
    <div className="flex flex-col overflow-hidden">
      <h2 className="px-3 py-2 text-sm font-semibold text-gray-500 uppercase tracking-wide">
        Tags ({sorted.length})
      </h2>
      <ul className="flex-1 overflow-y-auto" data-testid="tag-list">
        {sorted.map((pos) => (
          <li key={pos.tag_id}>
            <button
              type="button"
              className={`w-full text-left px-3 py-2 text-sm transition-colors hover:bg-gray-100 ${
                selectedTagId === pos.tag_id
                  ? "bg-blue-50 border-l-2 border-blue-600"
                  : ""
              }`}
              onClick={() => onSelectTag(pos.tag_id)}
            >
              <div className="font-medium text-gray-900">{pos.tag_id}</div>
              <div className="text-xs text-gray-500">
                {formatTime(pos.ts_utc_ms)}
              </div>
            </button>
          </li>
        ))}
        {sorted.length === 0 && (
          <li className="px-3 py-4 text-sm text-gray-400 text-center">
            No active tags
          </li>
        )}
      </ul>
    </div>
  );
}
