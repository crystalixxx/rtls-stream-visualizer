import { render, screen } from "@testing-library/react";
import type { Position } from "../../types";

function makePos(overrides: Partial<Position> = {}): Position {
  return {
    tag_id: "tag-001",
    ts_utc_ms: 1700000000000,
    source_type: "display",
    origin: "ls-1000",
    status: null,
    layer: 1,
    area: "zone-A",
    x: null,
    y: null,
    z: null,
    lng: 37.62,
    lat: 55.75,
    ...overrides,
  };
}

function buildPositions(...items: Position[]): Map<string, Position> {
  return new Map(items.map((p) => [p.tag_id, p]));
}

vi.mock("react-leaflet", () => {
  const MapContainer = ({ children, ...props }: any) => (
    <div data-testid="map-container" {...props}>
      {children}
    </div>
  );
  const TileLayer = () => <div data-testid="tile-layer" />;
  const Marker = ({ children, ...props }: any) => (
    <div data-testid={`marker-${props.position?.[0]}-${props.position?.[1]}`}>
      {children}
    </div>
  );
  const Tooltip = ({ children }: any) => (
    <div data-testid="tooltip">{children}</div>
  );
  const useMap = () => ({ flyTo: vi.fn(), getZoom: () => 13 });
  return { MapContainer, TileLayer, Marker, Tooltip, useMap };
});

vi.mock("leaflet", () => ({
  default: {
    divIcon: () => ({}),
  },
  divIcon: () => ({}),
}));

import { GeoMap } from "../GeoMap";

describe("GeoMap", () => {
  it("renders the map container", () => {
    render(
      <GeoMap
        positions={new Map()}
        selectedTagId={null}
        onSelectTag={() => {}}
        flyTo={null}
      />,
    );

    expect(screen.getByTestId("geo-map")).toBeInTheDocument();
  });

  it("renders markers for positions with lat/lng", () => {
    const positions = buildPositions(
      makePos({ tag_id: "g1", lat: 55.75, lng: 37.62 }),
      makePos({ tag_id: "g2", lat: 55.76, lng: 37.63 }),
    );

    render(
      <GeoMap
        positions={positions}
        selectedTagId={null}
        onSelectTag={() => {}}
        flyTo={null}
      />,
    );

    expect(screen.getByTestId("marker-55.75-37.62")).toBeInTheDocument();
    expect(screen.getByTestId("marker-55.76-37.63")).toBeInTheDocument();
  });

  it("does not render markers when showTags is false", () => {
    const positions = buildPositions(
      makePos({ tag_id: "g1", lat: 55.75, lng: 37.62 }),
    );

    render(
      <GeoMap
        positions={positions}
        selectedTagId={null}
        onSelectTag={() => {}}
        flyTo={null}
        showTags={false}
      />,
    );

    expect(screen.queryByTestId(/^marker-/)).not.toBeInTheDocument();
  });

  it("skips positions without lat/lng", () => {
    const positions = buildPositions(
      makePos({ tag_id: "g1", lat: 55.75, lng: 37.62 }),
      makePos({ tag_id: "indoor-only", lat: null, lng: null, x: 10, y: 20 }),
    );

    render(
      <GeoMap
        positions={positions}
        selectedTagId={null}
        onSelectTag={() => {}}
        flyTo={null}
      />,
    );

    expect(screen.getByTestId("marker-55.75-37.62")).toBeInTheDocument();
    expect(screen.queryByTestId(/marker-null/)).not.toBeInTheDocument();
  });

  it("renders tooltip with tag info", () => {
    const positions = buildPositions(
      makePos({ tag_id: "g1", lat: 55.75, lng: 37.62 }),
    );

    render(
      <GeoMap
        positions={positions}
        selectedTagId={null}
        onSelectTag={() => {}}
        flyTo={null}
      />,
    );

    expect(screen.getByText("g1")).toBeInTheDocument();
  });
});
