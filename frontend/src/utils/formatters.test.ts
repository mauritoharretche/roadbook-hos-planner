import { departureInputToUtcIso, formatDate, formatDateTime } from "./formatters";

test("treats datetime-local departure input as an explicit UTC timestamp", () => {
  expect(departureInputToUtcIso("2026-10-07T08:30")).toBe("2026-10-07T08:30:00.000Z");
});

test("formats explicit UTC timestamps and dates in UTC", () => {
  const timestamp = "2026-10-07T00:30:00Z";
  const expectedTime = new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(timestamp));
  const expectedDate = new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date("2026-10-07T12:00:00Z"));

  expect(formatDateTime(timestamp)).toBe(`${expectedTime} UTC`);
  expect(formatDate("2026-10-07")).toBe(expectedDate);
});
