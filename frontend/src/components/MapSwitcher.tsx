import type { MapMode } from "../types";

interface Props {
  mode: MapMode;
  onChange: (mode: MapMode) => void;
}

export function MapSwitcher({ mode, onChange }: Props) {
  return (
    <div className="inline-flex rounded-lg border border-gray-300 bg-white text-sm">
      <button
        type="button"
        className={`px-4 py-1.5 rounded-l-lg transition-colors ${
          mode === "indoor"
            ? "bg-blue-600 text-white"
            : "text-gray-700 hover:bg-gray-100"
        }`}
        onClick={() => onChange("indoor")}
      >
        Indoor
      </button>
      <button
        type="button"
        className={`px-4 py-1.5 rounded-r-lg transition-colors ${
          mode === "geo"
            ? "bg-blue-600 text-white"
            : "text-gray-700 hover:bg-gray-100"
        }`}
        onClick={() => onChange("geo")}
      >
        Geo
      </button>
    </div>
  );
}
