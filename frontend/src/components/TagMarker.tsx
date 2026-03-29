import type { Position } from "../types";

interface Props {
  position: Position;
  coordSystem: "indoor" | "geo";
  selected?: boolean;
  onClick?: () => void;
}

function formatTime(ms: number): string {
  return new Date(ms).toLocaleTimeString();
}

function formatCoords(
  position: Position,
  coordSystem: "indoor" | "geo",
): string {
  if (coordSystem === "indoor") {
    const { x, y } = position;
    if (x != null && y != null) {
      return `x: ${x.toFixed(1)} m, y: ${y.toFixed(1)} m`;
    }
    return "no coords";
  }
  const { lng, lat } = position;
  if (lng != null && lat != null) {
    return `lng: ${lng.toFixed(5)}, lat: ${lat.toFixed(5)}`;
  }
  return "no coords";
}

export function TagMarker({
  position,
  coordSystem,
  selected,
  onClick,
}: Props) {
  const { tag_id, ts_utc_ms } = position;

  return (
    <div
      data-testid={`tag-marker-${tag_id}`}
      className="group relative cursor-pointer"
      onClick={onClick}
    >
      <div
        className={`h-4 w-4 rounded-full border-2 border-white shadow ${
          selected ? "bg-orange-500" : "bg-blue-500"
        }`}
      />
      <div className="pointer-events-none absolute bottom-full left-1/2 mb-2 -translate-x-1/2 whitespace-nowrap rounded bg-gray-900 px-2 py-1 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100">
        <div className="font-medium">{tag_id}</div>
        <div>{formatCoords(position, coordSystem)}</div>
        <div>{formatTime(ts_utc_ms)}</div>
      </div>
    </div>
  );
}
