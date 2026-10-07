import type { DailyLog, TripEvent, TripPlan } from "../types/trip";

export const drivingEvent: TripEvent = {
  event_type: "DRIVING",
  duty_status: "DRIVING",
  start: "2026-01-05T08:00:00Z",
  end: "2026-01-05T09:00:00Z",
  duration_minutes: 60,
  route_progress_miles: 0,
  reason: "Route driving",
  segment_index: 0,
  segment_name: "Current location to pickup",
};

export const pickupEvent: TripEvent = {
  event_type: "PICKUP",
  duty_status: "ON_DUTY_NOT_DRIVING",
  start: "2026-01-05T09:00:00Z",
  end: "2026-01-05T10:00:00Z",
  duration_minutes: 60,
  route_progress_miles: 50,
  reason: "Required pickup service",
  segment_index: 0,
  segment_name: "Current location to pickup",
};

export const dailyLogFixture: DailyLog = {
  date: "2026-01-05",
  driving_minutes: 60,
  on_duty_not_driving_minutes: 60,
  off_duty_minutes: 0,
  sleeper_berth_minutes: 0,
  total_minutes: 120,
  events: [drivingEvent, pickupEvent],
};

export const tripPlanFixture: TripPlan = {
  status: "feasible",
  route: {
    distance_miles: 50,
    duration_minutes: 60,
    geometry: [[-57.9544, -34.9214], [-58.3816, -34.6037]],
    legs: [{ start_label: "Current", end_label: "Pickup", distance_miles: 50, duration_minutes: 60 }],
    waypoints: [
      { kind: "current", label: "Current", latitude: -34.9214, longitude: -57.9544 },
      { kind: "pickup", label: "Pickup", latitude: -34.6037, longitude: -58.3816 },
      { kind: "dropoff", label: "Dropoff", latitude: -32.9442, longitude: -60.6505 },
    ],
  },
  events: [drivingEvent, pickupEvent],
  stops: [pickupEvent],
  daily_logs: [dailyLogFixture],
  summary: {
    total_distance_miles: 50,
    completed_distance_miles: 50,
    total_driving_minutes: 60,
    total_on_duty_minutes: 120,
    total_off_duty_minutes: 0,
    cycle_hours_used: 12,
    cycle_hours_remaining: 58,
    warnings: [],
  },
  error: null,
};
