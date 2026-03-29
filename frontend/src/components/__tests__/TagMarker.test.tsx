import { render, screen } from "@testing-library/react";
import { TagMarker } from "../TagMarker";
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
    x: 10.5,
    y: 20.3,
    z: 0.0,
    lng: null,
    lat: null,
    ...overrides,
  };
}

describe("TagMarker", () => {
  it("renders marker with tag_id in tooltip", () => {
    render(<TagMarker position={makePos()} coordSystem="indoor" />);

    expect(screen.getByTestId("tag-marker-tag-001")).toBeInTheDocument();
    expect(screen.getByText("tag-001")).toBeInTheDocument();
  });

  it("shows x/y in meters for indoor coordSystem", () => {
    render(
      <TagMarker
        position={makePos({ x: 10.5, y: 20.3 })}
        coordSystem="indoor"
      />,
    );

    expect(screen.getByText("x: 10.5 m, y: 20.3 m")).toBeInTheDocument();
  });

  it("shows lng/lat for geo coordSystem", () => {
    render(
      <TagMarker
        position={makePos({ lng: 37.61234, lat: 55.75678 })}
        coordSystem="geo"
      />,
    );

    expect(
      screen.getByText("lng: 37.61234, lat: 55.75678"),
    ).toBeInTheDocument();
  });

  it("does not mix coordinate systems: indoor ignores lng/lat", () => {
    render(
      <TagMarker
        position={makePos({
          x: 10.5,
          y: 20.3,
          lng: 37.61234,
          lat: 55.75678,
        })}
        coordSystem="indoor"
      />,
    );

    expect(screen.getByText("x: 10.5 m, y: 20.3 m")).toBeInTheDocument();
    expect(screen.queryByText(/lng:/)).not.toBeInTheDocument();
  });

  it("does not mix coordinate systems: geo ignores x/y", () => {
    render(
      <TagMarker
        position={makePos({
          x: 10.5,
          y: 20.3,
          lng: 37.61234,
          lat: 55.75678,
        })}
        coordSystem="geo"
      />,
    );

    expect(
      screen.getByText("lng: 37.61234, lat: 55.75678"),
    ).toBeInTheDocument();
    expect(screen.queryByText(/x: 10.5/)).not.toBeInTheDocument();
  });

  it("shows 'no coords' when indoor has no x/y", () => {
    render(
      <TagMarker
        position={makePos({ x: null, y: null })}
        coordSystem="indoor"
      />,
    );

    expect(screen.getByText("no coords")).toBeInTheDocument();
  });

  it("shows 'no coords' when geo has no lng/lat", () => {
    render(
      <TagMarker
        position={makePos({ lng: null, lat: null })}
        coordSystem="geo"
      />,
    );

    expect(screen.getByText("no coords")).toBeInTheDocument();
  });

  it("applies selected style when selected", () => {
    const { container } = render(
      <TagMarker position={makePos()} coordSystem="indoor" selected={true} />,
    );

    const dot = container.querySelector(".rounded-full");
    expect(dot?.className).toContain("bg-orange-500");
  });

  it("applies default style when not selected", () => {
    const { container } = render(
      <TagMarker position={makePos()} coordSystem="indoor" selected={false} />,
    );

    const dot = container.querySelector(".rounded-full");
    expect(dot?.className).toContain("bg-blue-500");
  });
});
