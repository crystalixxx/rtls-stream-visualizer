import { render, screen } from "@testing-library/react";
import { ConnectionStatus } from "../ConnectionStatus";
import type { WsState } from "../../types";

describe("ConnectionStatus", () => {
  const cases: [WsState, string, string][] = [
    ["connected", "Connected", "bg-green-500"],
    ["connecting", "Connecting…", "bg-yellow-500"],
    ["reconnecting", "Reconnecting…", "bg-yellow-500"],
    ["disconnected", "Disconnected", "bg-red-500"],
  ];

  it.each(cases)(
    'renders "%s" state with label "%s" and dot class "%s"',
    (state, label, dotClass) => {
      render(<ConnectionStatus state={state} />);

      expect(screen.getByTestId("status-label")).toHaveTextContent(label);
      expect(screen.getByTestId("status-dot").className).toContain(dotClass);
    },
  );
});
