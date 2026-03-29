import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LayerToggles } from "../LayerToggles";

describe("LayerToggles", () => {
  it("renders checkboxes with correct checked state", () => {
    render(
      <LayerToggles
        layers={{ tags: true, anchors: false }}
        onChange={() => {}}
      />,
    );

    const tagsCheckbox = screen.getByTestId("toggle-tags") as HTMLInputElement;
    const anchorsCheckbox = screen.getByTestId(
      "toggle-anchors",
    ) as HTMLInputElement;

    expect(tagsCheckbox.checked).toBe(true);
    expect(anchorsCheckbox.checked).toBe(false);
  });

  it("calls onChange when toggling tags off", async () => {
    const onChange = vi.fn();
    render(
      <LayerToggles
        layers={{ tags: true, anchors: true }}
        onChange={onChange}
      />,
    );

    await userEvent.click(screen.getByTestId("toggle-tags"));

    expect(onChange).toHaveBeenCalledWith({ tags: false, anchors: true });
  });

  it("calls onChange when toggling anchors on", async () => {
    const onChange = vi.fn();
    render(
      <LayerToggles
        layers={{ tags: true, anchors: false }}
        onChange={onChange}
      />,
    );

    await userEvent.click(screen.getByTestId("toggle-anchors"));

    expect(onChange).toHaveBeenCalledWith({ tags: true, anchors: true });
  });
});
