import { render, screen } from "@testing-library/react";

import { tripPlanFixture } from "../../test/fixtures";
import { TripSummary } from "./TripSummary";

test("renders infeasible plan feedback from the API", () => {
  const plan = {
    ...tripPlanFixture,
    status: "infeasible" as const,
    error: { code: "CYCLE_CAPACITY_EXHAUSTED", message: "The trip cannot finish within the available cycle." },
  };
  render(<TripSummary plan={plan} />);

  expect(screen.getByText("Plan not compliant")).toBeInTheDocument();
  expect(screen.getByText("The trip cannot finish within the available cycle.")).toBeInTheDocument();
  expect(screen.getByText("Infeasible")).toBeInTheDocument();
});
