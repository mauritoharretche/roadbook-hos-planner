import { render, screen } from "@testing-library/react";

import { drivingEvent, pickupEvent } from "../../test/fixtures";
import { StopTimeline } from "./StopTimeline";

test("orders timeline events chronologically", () => {
  render(<StopTimeline events={[pickupEvent, drivingEvent]} />);

  expect(screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent)).toEqual([
    "Driving",
    "Pickup",
  ]);
});
