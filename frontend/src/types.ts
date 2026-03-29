export interface Position {
  tag_id: string;
  ts_utc_ms: number;
  source_type: string;
  origin: string;
  status: string | null;
  layer: number | null;
  area: string | null;
  x: number | null;
  y: number | null;
  z: number | null;
  lng: number | null;
  lat: number | null;
}

export type WsState =
  | "connecting"
  | "connected"
  | "reconnecting"
  | "disconnected";

export type MapMode = "indoor" | "geo";

export type AppMode = "live" | "history";
