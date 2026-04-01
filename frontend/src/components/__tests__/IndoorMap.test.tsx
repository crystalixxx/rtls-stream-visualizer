import { render, screen } from "@testing-library/react";
import { IndoorMap } from "../IndoorMap";
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
    x: 100,
    y: 200,
    z: 0,
    lng: null,
    lat: null,
    ...overrides,
  };
}

function buildPositions(...items: Position[]): Map<string, Position> {
  return new Map(items.map((p) => [p.tag_id, p]));
}

describe("IndoorMap", () => {
  it("renders the floor plan image", () => {
    render(
      <IndoorMap
        positions={new Map()}
        selectedTagId={null}
        onSelectTag={() => {}}
      />,
    );

    expect(screen.getByAltText("Floor plan")).toBeInTheDocument();
  });

  it("renders markers for positions with x/y", () => {
    const positions = buildPositions(
      makePos({ tag_id: "t1", x: 50, y: 60 }),
      makePos({ tag_id: "t2", x: 150, y: 250 }),
    );

    render(
      <IndoorMap
        positions={positions}
        selectedTagId={null}
        onSelectTag={() => {}}
      />,
    );

    expect(screen.getByTestId("tag-marker-t1")).toBeInTheDocument();
    expect(screen.getByTestId("tag-marker-t2")).toBeInTheDocument();
  });

  it("does not render markers when showTags is false", () => {
    const positions = buildPositions(makePos({ tag_id: "t1" }));

    render(
      <IndoorMap
        positions={positions}
        selectedTagId={null}
        onSelectTag={() => {}}
        showTags={false}
      />,
    );

    expect(screen.queryByTestId("tag-marker-t1")).not.toBeInTheDocument();
  });

  it("skips positions without x/y", () => {
    const positions = buildPositions(
      makePos({ tag_id: "t-indoor", x: 10, y: 20 }),
      makePos({ tag_id: "t-geo", x: null, y: null, lng: 37.6, lat: 55.7 }),
    );

    render(
      <IndoorMap
        positions={positions}
        selectedTagId={null}
        onSelectTag={() => {}}
      />,
    );

    expect(screen.getByTestId("tag-marker-t-indoor")).toBeInTheDocument();
    expect(screen.queryByTestId("tag-marker-t-geo")).not.toBeInTheDocument();
  });

  it("renders the indoor-map container", () => {
    render(
      <IndoorMap
        positions={new Map()}
        selectedTagId={null}
        onSelectTag={() => {}}
      />,
    );

    expect(screen.getByTestId("indoor-map")).toBeInTheDocument();
  });
});
