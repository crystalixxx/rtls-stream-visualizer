import type { WsState } from "../types";

const CONFIG: Record<WsState, { label: string; color: string }> = {
  connected: { label: "Connected", color: "bg-green-500" },
  connecting: { label: "Connecting…", color: "bg-yellow-500" },
  reconnecting: { label: "Reconnecting…", color: "bg-yellow-500" },
  disconnected: { label: "Disconnected", color: "bg-red-500" },
};

interface Props {
  state: WsState;
}

export function ConnectionStatus({ state }: Props) {
  const { label, color } = CONFIG[state];

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 text-sm">
      <span
        data-testid="status-dot"
        className={`inline-block h-2.5 w-2.5 rounded-full ${color}`}
      />
      <span data-testid="status-label">{label}</span>
    </div>
  );
}
