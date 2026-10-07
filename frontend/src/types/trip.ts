export type PlanStatus = "feasible" | "infeasible";

export type DutyStatus =
  | "DRIVING"
  | "ON_DUTY_NOT_DRIVING"
  | "OFF_DUTY"
  | "SLEEPER_BERTH";

export interface RouteLeg {
  start_label: string;
  end_label: string;
  distance_miles: number;
  duration_minutes: number;
}

export interface RouteWaypoint {
  kind: "current" | "pickup" | "dropoff";
  label: string;
  latitude: number;
  longitude: number;
}

export interface Route {
  distance_miles: number;
  duration_minutes: number;
  geometry: [number, number][];
  legs: RouteLeg[];
  waypoints: RouteWaypoint[];
}

export interface TripEvent {
  event_type: "DRIVING" | "PICKUP" | "DROPOFF" | "FUEL" | "BREAK_30_MIN" | "REST_10_HOURS";
  duty_status: DutyStatus;
  start: string;
  end: string;
  duration_minutes: number;
  route_progress_miles: number;
  reason: string;
  segment_index: number | null;
  segment_name: string | null;
}

export interface DailyLog {
  date: string;
  driving_minutes: number;
  on_duty_not_driving_minutes: number;
  off_duty_minutes: number;
  sleeper_berth_minutes: number;
  total_minutes: number;
  events: TripEvent[];
}

export interface TripSummary {
  total_distance_miles: number;
  completed_distance_miles: number;
  total_driving_minutes: number;
  total_on_duty_minutes: number;
  total_off_duty_minutes: number;
  cycle_hours_used: number;
  cycle_hours_remaining: number;
  warnings: string[];
}

export interface PlanError {
  code: string;
  message: string;
}

export interface TripPlan {
  status: PlanStatus;
  route: Route;
  events: TripEvent[];
  stops: TripEvent[];
  daily_logs: DailyLog[];
  summary: TripSummary;
  error: PlanError | null;
}

export interface TripPlanRequest {
  current_location: string;
  pickup_location: string;
  dropoff_location: string;
  current_cycle_used_hours: number;
  departure_at?: string;
}
