import { render, screen } from "@testing-library/react";

import { dailyLogFixture } from "../../test/fixtures";
import { DailyLogTabs } from "./DailyLogTabs";

test("renders daily totals and event list", () => {
  render(<DailyLogTabs dailyLogs={[dailyLogFixture]} />);

  expect(screen.getByText("Duty status by day")).toBeInTheDocument();
  expect(screen.getByText("Events").parentElement).toHaveTextContent("Events2");
  expect(screen.getAllByText("Driving")).toHaveLength(2);
  expect(screen.getByText("Pickup")).toBeInTheDocument();
});
