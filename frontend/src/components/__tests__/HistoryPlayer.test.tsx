import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HistoryPlayer } from "../HistoryPlayer";

const baseProps = {
  tagIds: ["tag-001", "tag-002"],
  playing: false,
  speed: 1 as const,
  progress: 0,
  currentTimeMs: null,
  timeRange: null,
  onPlay: vi.fn(),
  onPause: vi.fn(),
  onSetSpeed: vi.fn(),
  onSeek: vi.fn(),
  onLoad: vi.fn(),
  onReset: vi.fn(),
};

describe("HistoryPlayer", () => {
  it("renders tag checkboxes", () => {
    render(<HistoryPlayer {...baseProps} />);

    expect(screen.getByTestId("history-tag-tag-001")).toBeInTheDocument();
    expect(screen.getByTestId("history-tag-tag-002")).toBeInTheDocument();
  });

  it("disables load button when no tags selected", () => {
    render(<HistoryPlayer {...baseProps} />);

    const loadBtn = screen.getByTestId("history-load") as HTMLButtonElement;
    expect(loadBtn.disabled).toBe(true);
  });

  it("enables load button when a tag is selected", async () => {
    render(<HistoryPlayer {...baseProps} />);

    await userEvent.click(screen.getByTestId("history-tag-tag-001"));

    const loadBtn = screen.getByTestId("history-load") as HTMLButtonElement;
    expect(loadBtn.disabled).toBe(false);
  });

  it("shows playback controls when timeRange is set", () => {
    render(
      <HistoryPlayer
        {...baseProps}
        timeRange={{ start: 1000, end: 5000 }}
        currentTimeMs={2000}
      />,
    );

    expect(screen.getByTestId("history-play-pause")).toBeInTheDocument();
    expect(screen.getByTestId("history-speed")).toBeInTheDocument();
    expect(screen.getByTestId("history-slider")).toBeInTheDocument();
  });

  it("does not show playback controls when no data loaded", () => {
    render(<HistoryPlayer {...baseProps} />);

    expect(screen.queryByTestId("history-play-pause")).not.toBeInTheDocument();
  });

  it("shows Play when not playing, Pause when playing", () => {
    const { rerender } = render(
      <HistoryPlayer
        {...baseProps}
        playing={false}
        timeRange={{ start: 0, end: 1000 }}
        currentTimeMs={0}
      />,
    );

    expect(screen.getByTestId("history-play-pause")).toHaveTextContent("Play");

    rerender(
      <HistoryPlayer
        {...baseProps}
        playing={true}
        timeRange={{ start: 0, end: 1000 }}
        currentTimeMs={500}
      />,
    );

    expect(screen.getByTestId("history-play-pause")).toHaveTextContent("Pause");
  });

  it("calls onPlay when clicking Play", async () => {
    const onPlay = vi.fn();
    render(
      <HistoryPlayer
        {...baseProps}
        onPlay={onPlay}
        playing={false}
        timeRange={{ start: 0, end: 1000 }}
        currentTimeMs={0}
      />,
    );

    await userEvent.click(screen.getByTestId("history-play-pause"));

    expect(onPlay).toHaveBeenCalled();
  });

  it("calls onReset when clicking Reset", async () => {
    const onReset = vi.fn();
    render(<HistoryPlayer {...baseProps} onReset={onReset} />);

    await userEvent.click(screen.getByTestId("history-reset"));

    expect(onReset).toHaveBeenCalled();
  });

  it("shows empty state when no tags available", () => {
    render(<HistoryPlayer {...baseProps} tagIds={[]} />);

    expect(screen.getByText("No tags available")).toBeInTheDocument();
  });
});
