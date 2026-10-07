import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { TripForm } from "./TripForm";

test("shows client validation errors instead of submitting incomplete form data", () => {
  const onSubmit = vi.fn();
  render(<TripForm isLoading={false} onSubmit={onSubmit} />);

  fireEvent.change(screen.getByLabelText("Current location"), { target: { value: "" } });
  fireEvent.change(screen.getByLabelText("Current cycle used (hours)"), { target: { value: "72" } });
  fireEvent.click(screen.getByRole("button", { name: "Calculate trip" }));

  expect(screen.getByText("This location is required.")).toBeInTheDocument();
  expect(screen.getByText("Enter a cycle value between 0 and 70 hours.")).toBeInTheDocument();
  expect(onSubmit).not.toHaveBeenCalled();
});
