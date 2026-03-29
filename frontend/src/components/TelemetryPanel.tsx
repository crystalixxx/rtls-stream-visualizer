interface Props {
  eventsPerSec: number;
  lastEventTs: number | null;
  activeTagCount: number;
}

function formatLag(lastEventTs: number | null): string {
  if (lastEventTs === null) return "--";
  const lag = Date.now() - lastEventTs;
  if (lag < 1000) return `${lag} ms`;
  return `${(lag / 1000).toFixed(1)} s`;
}

export function TelemetryPanel({
  eventsPerSec,
  lastEventTs,
  activeTagCount,
}: Props) {
  return (
    <div
      className="grid grid-cols-3 gap-1 border-b border-gray-200 px-3 py-2 text-center text-xs"
      data-testid="telemetry-panel"
    >
      <div>
        <div className="text-gray-400">Events/s</div>
        <div className="font-semibold text-gray-800" data-testid="eps">
          {eventsPerSec}
        </div>
      </div>
      <div>
        <div className="text-gray-400">Lag</div>
        <div className="font-semibold text-gray-800" data-testid="lag">
          {formatLag(lastEventTs)}
        </div>
      </div>
      <div>
        <div className="text-gray-400">Tags</div>
        <div className="font-semibold text-gray-800" data-testid="tag-count">
          {activeTagCount}
        </div>
      </div>
    </div>
  );
}
