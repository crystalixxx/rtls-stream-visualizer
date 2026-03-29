import {
  MapContainer,
  TileLayer,
  Marker,
  Tooltip,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import type { Position } from "../types";
import { useEffect } from "react";

const DEFAULT_CENTER: [number, number] = [55.75, 37.62];
const DEFAULT_ZOOM = 13;

function createIcon(selected: boolean): L.DivIcon {
  const color = selected ? "#f97316" : "#3b82f6";
  return L.divIcon({
    className: "",
    iconSize: [16, 16],
    iconAnchor: [8, 8],
    html: `<div style="width:16px;height:16px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,.3)"></div>`,
  });
}

function FlyTo({ center }: { center: [number, number] | null }) {
  const map = useMap();
  useEffect(() => {
    if (center) map.flyTo(center, map.getZoom());
  }, [center, map]);
  return null;
}

interface Props {
  positions: Map<string, Position>;
  selectedTagId: string | null;
  onSelectTag: (tagId: string) => void;
  flyTo: [number, number] | null;
  showTags?: boolean;
}

function formatTime(ms: number): string {
  return new Date(ms).toLocaleTimeString();
}

export function GeoMap({
  positions,
  selectedTagId,
  onSelectTag,
  flyTo,
  showTags = true,
}: Props) {
  const geoPositions = Array.from(positions.values()).filter(
    (p) => p.lat != null && p.lng != null,
  );

  return (
    <MapContainer
      center={DEFAULT_CENTER}
      zoom={DEFAULT_ZOOM}
      className="h-full w-full"
      data-testid="geo-map"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FlyTo center={flyTo} />
      {showTags &&
        geoPositions.map((pos) => (
          <Marker
            key={pos.tag_id}
            position={[pos.lat!, pos.lng!]}
            icon={createIcon(selectedTagId === pos.tag_id)}
            eventHandlers={{ click: () => onSelectTag(pos.tag_id) }}
          >
            <Tooltip>
              <div className="text-xs">
                <div className="font-medium">{pos.tag_id}</div>
                <div>
                  lat: {pos.lat!.toFixed(5)}, lng: {pos.lng!.toFixed(5)}
                </div>
                <div>{formatTime(pos.ts_utc_ms)}</div>
              </div>
            </Tooltip>
          </Marker>
        ))}
    </MapContainer>
  );
}
