import { render, screen } from "@testing-library/react";
import { TelemetryPanel } from "../TelemetryPanel";

describe("TelemetryPanel", () => {
  it("renders events per second", () => {
    render(
      <TelemetryPanel eventsPerSec={42} lastEventTs={null} activeTagCount={0} />,
    );

    expect(screen.getByTestId("eps")).toHaveTextContent("42");
  });

  it("renders active tag count", () => {
    render(
      <TelemetryPanel eventsPerSec={0} lastEventTs={null} activeTagCount={5} />,
    );

    expect(screen.getByTestId("tag-count")).toHaveTextContent("5");
  });

  it("renders '--' lag when no events received", () => {
    render(
      <TelemetryPanel eventsPerSec={0} lastEventTs={null} activeTagCount={0} />,
    );

    expect(screen.getByTestId("lag")).toHaveTextContent("--");
  });

  it("renders lag in ms when event is recent", () => {
    const now = Date.now();
    render(
      <TelemetryPanel
        eventsPerSec={1}
        lastEventTs={now - 150}
        activeTagCount={1}
      />,
    );

    const lagText = screen.getByTestId("lag").textContent!;
    expect(lagText).toMatch(/\d+ ms/);
  });
});
