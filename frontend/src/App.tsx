import { useCallback, useState } from "react";
import type { AppMode, MapMode } from "./types";
import { usePositions } from "./hooks/usePositions";
import { useHistoryPlayer } from "./hooks/useHistoryPlayer";
import { ConnectionStatus } from "./components/ConnectionStatus";
import { TelemetryPanel } from "./components/TelemetryPanel";
import { LayerToggles, type VisibleLayers } from "./components/LayerToggles";
import { MapSwitcher } from "./components/MapSwitcher";
import { TagList } from "./components/TagList";
import { IndoorMap } from "./components/IndoorMap";
import { GeoMap } from "./components/GeoMap";
import { HistoryPlayer } from "./components/HistoryPlayer";

export default function App() {
  const { positions, connectionState, eventsPerSec, lastEventTs } =
    usePositions();
  const player = useHistoryPlayer();

  const [appMode, setAppMode] = useState<AppMode>("live");
  const [mapMode, setMapMode] = useState<MapMode>("indoor");
  const [selectedTagId, setSelectedTagId] = useState<string | null>(null);
  const [flyTo, setFlyTo] = useState<[number, number] | null>(null);
  const [invertY, setInvertY] = useState(false);
  const [visibleLayers, setVisibleLayers] = useState<VisibleLayers>({
    tags: true,
    anchors: true,
  });

  const displayPositions =
    appMode === "history" ? player.currentPositions : positions;

  const handleSelectTag = useCallback(
    (tagId: string) => {
      setSelectedTagId(tagId);
      const pos = displayPositions.get(tagId);
      if (pos && mapMode === "geo" && pos.lat != null && pos.lng != null) {
        setFlyTo([pos.lat, pos.lng]);
      }
    },
    [displayPositions, mapMode],
  );

  const handleSwitchAppMode = useCallback(
    (mode: AppMode) => {
      setAppMode(mode);
      if (mode === "live") player.reset();
    },
    [player],
  );

  const tagIds = Array.from(positions.keys()).sort();

  return (
    <div className="flex h-full bg-white">
      <aside className="flex w-64 flex-col border-r border-gray-200 bg-white">
        <div className="flex items-center justify-between border-b border-gray-200 px-3 py-2">
          <h1 className="text-sm font-bold text-gray-800">RTLS Visualizer</h1>
          <ConnectionStatus state={connectionState} />
        </div>

        <TelemetryPanel
          eventsPerSec={eventsPerSec}
          lastEventTs={lastEventTs}
          activeTagCount={positions.size}
        />

        <LayerToggles layers={visibleLayers} onChange={setVisibleLayers} />

        <div className="flex border-b border-gray-200">
          <button
            type="button"
            className={`flex-1 px-2 py-1.5 text-xs font-medium transition-colors ${
              appMode === "live"
                ? "bg-blue-50 text-blue-700 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
            onClick={() => handleSwitchAppMode("live")}
          >
            Live
          </button>
          <button
            type="button"
            className={`flex-1 px-2 py-1.5 text-xs font-medium transition-colors ${
              appMode === "history"
                ? "bg-blue-50 text-blue-700 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
            onClick={() => handleSwitchAppMode("history")}
          >
            History
          </button>
        </div>

        <div className="flex-1 overflow-hidden">
          {appMode === "live" ? (
            <TagList
              positions={displayPositions}
              selectedTagId={selectedTagId}
              onSelectTag={handleSelectTag}
            />
          ) : (
            <HistoryPlayer
              tagIds={tagIds}
              playing={player.playing}
              speed={player.speed}
              progress={player.progress}
              currentTimeMs={player.currentTimeMs}
              timeRange={player.timeRange}
              onPlay={player.play}
              onPause={player.pause}
              onSetSpeed={player.setSpeed}
              onSeek={player.seek}
              onLoad={player.load}
              onReset={player.reset}
            />
          )}
        </div>
      </aside>

      <main className="relative flex-1">
        <div className="absolute top-3 right-3 z-[1000] flex items-center gap-2">
          {mapMode === "indoor" && (
            <button
              type="button"
              onClick={() => setInvertY((v) => !v)}
              className={`rounded border px-2 py-1 text-xs transition-colors ${
                invertY
                  ? "border-blue-600 bg-blue-600 text-white"
                  : "border-gray-300 bg-white text-gray-700 hover:bg-gray-100"
              }`}
              title="Invert Y axis"
            >
              Invert Y
            </button>
          )}
          <MapSwitcher mode={mapMode} onChange={setMapMode} />
        </div>

        {mapMode === "indoor" ? (
          <IndoorMap
            positions={displayPositions}
            selectedTagId={selectedTagId}
            onSelectTag={handleSelectTag}
            showTags={visibleLayers.tags}
            invertY={invertY}
          />
        ) : (
          <GeoMap
            positions={displayPositions}
            selectedTagId={selectedTagId}
            onSelectTag={handleSelectTag}
            flyTo={flyTo}
            showTags={visibleLayers.tags}
          />
        )}

        {appMode === "history" && (
          <div className="pointer-events-none absolute inset-0 bg-amber-50/20 z-[999]" />
        )}
      </main>
    </div>
  );
}
