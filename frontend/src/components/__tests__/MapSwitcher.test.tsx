import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MapSwitcher } from "../MapSwitcher";

describe("MapSwitcher", () => {
  it("highlights the active mode", () => {
    render(<MapSwitcher mode="indoor" onChange={() => {}} />);

    const indoorBtn = screen.getByText("Indoor");
    const geoBtn = screen.getByText("Geo");

    expect(indoorBtn.className).toContain("bg-blue-600");
    expect(geoBtn.className).not.toContain("bg-blue-600");
  });

  it("calls onChange when clicking the other mode", async () => {
    const onChange = vi.fn();
    render(<MapSwitcher mode="indoor" onChange={onChange} />);

    await userEvent.click(screen.getByText("Geo"));

    expect(onChange).toHaveBeenCalledWith("geo");
  });

  it("calls onChange with indoor when clicking Indoor", async () => {
    const onChange = vi.fn();
    render(<MapSwitcher mode="geo" onChange={onChange} />);

    await userEvent.click(screen.getByText("Indoor"));

    expect(onChange).toHaveBeenCalledWith("indoor");
  });
});
