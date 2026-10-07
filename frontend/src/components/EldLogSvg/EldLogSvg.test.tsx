import { render, screen } from "@testing-library/react";

import type { DailyLog, TripEvent } from "../../types/trip";
import { dailyLogFixture, drivingEvent, pickupEvent } from "../../test/fixtures";
import { EldLogSvg } from "./EldLogSvg";

function dailyLog(events: TripEvent[]): DailyLog {
  return { ...dailyLogFixture, events };
}

test("empty day renders a complete 24-hour off-duty graph", () => {
  render(<EldLogSvg dailyLog={dailyLog([])} />);

  const [offDuty] = screen.getAllByTestId("duty-segment");
  expect(offDuty).toHaveAttribute("data-status", "OFF_DUTY");
  expect(offDuty).toHaveAttribute("data-start-minute", "0");
  expect(offDuty).toHaveAttribute("data-end-minute", "1440");
});

test("places a driving event in the driving row at its correct time", () => {
  render(<EldLogSvg dailyLog={dailyLog([drivingEvent])} />);

  const driving = screen.getAllByTestId("duty-segment").find((node) => node.getAttribute("data-status") === "DRIVING");
  expect(driving).toHaveAttribute("data-start-minute", "480");
  expect(driving).toHaveAttribute("data-end-minute", "540");
});

test("renders duty transitions and off-duty gaps", () => {
  render(<EldLogSvg dailyLog={dailyLog([drivingEvent, pickupEvent])} />);

  expect(screen.getAllByTestId("duty-transition")).toHaveLength(3);
  expect(screen.getAllByTestId("duty-segment").some((node) => node.getAttribute("data-status") === "OFF_DUTY")).toBe(true);
});

test("clips an event crossing midnight to the current day", () => {
  const overnight = {
    ...drivingEvent,
    start: "2026-01-05T23:30:00Z",
    end: "2026-01-06T01:00:00Z",
  };
  render(<EldLogSvg dailyLog={dailyLog([overnight])} />);

  const driving = screen.getAllByTestId("duty-segment").find((node) => node.getAttribute("data-status") === "DRIVING");
  expect(driving).toHaveAttribute("data-start-minute", "1410");
  expect(driving).toHaveAttribute("data-end-minute", "1440");
});

test("sorts multiple events without mutating API data and displays API totals", () => {
  const source = dailyLog([pickupEvent, drivingEvent]);
  const before = JSON.stringify(source);
  render(<EldLogSvg dailyLog={source} />);

  const statuses = screen.getAllByTestId("duty-segment").map((node) => node.getAttribute("data-status"));
  expect(statuses).toEqual(["OFF_DUTY", "DRIVING", "ON_DUTY_NOT_DRIVING", "OFF_DUTY"]);
  expect(JSON.stringify(source)).toBe(before);
  expect(screen.getByText("Driving 1.0 h")).toBeInTheDocument();
  expect(screen.getByText("On duty 1.0 h")).toBeInTheDocument();
});
