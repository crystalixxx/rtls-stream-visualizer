import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TagList } from "../TagList";
import type { Position } from "../../types";

function makePos(tag_id: string, ts: number): Position {
  return {
    tag_id,
    ts_utc_ms: ts,
    source_type: "json",
    origin: "test",
    status: null,
    layer: null,
    area: null,
    x: 0,
    y: 0,
    z: null,
    lng: null,
    lat: null,
  };
}

describe("TagList", () => {
  it("renders all tags sorted alphabetically", () => {
    const positions = new Map<string, Position>([
      ["b-tag", makePos("b-tag", 2000)],
      ["a-tag", makePos("a-tag", 1000)],
    ]);

    render(
      <TagList
        positions={positions}
        selectedTagId={null}
        onSelectTag={() => {}}
      />,
    );

    const items = screen.getAllByRole("button");
    expect(items[0]).toHaveTextContent("a-tag");
    expect(items[1]).toHaveTextContent("b-tag");
  });

  it("fires onSelectTag when clicking a tag", async () => {
    const onSelect = vi.fn();
    const positions = new Map([["t1", makePos("t1", 1000)]]);

    render(
      <TagList
        positions={positions}
        selectedTagId={null}
        onSelectTag={onSelect}
      />,
    );

    await userEvent.click(screen.getByText("t1"));

    expect(onSelect).toHaveBeenCalledWith("t1");
  });

  it("shows empty state when no tags", () => {
    render(
      <TagList
        positions={new Map()}
        selectedTagId={null}
        onSelectTag={() => {}}
      />,
    );

    expect(screen.getByText("No active tags")).toBeInTheDocument();
  });

  it("displays tag count in header", () => {
    const positions = new Map([
      ["t1", makePos("t1", 1000)],
      ["t2", makePos("t2", 2000)],
    ]);

    render(
      <TagList
        positions={positions}
        selectedTagId={null}
        onSelectTag={() => {}}
      />,
    );

    expect(screen.getByText("Tags (2)")).toBeInTheDocument();
  });
});
