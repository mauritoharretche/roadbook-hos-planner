import { postJson } from "./client";
import type { TripPlan, TripPlanRequest } from "../types/trip";

export function planTrip(request: TripPlanRequest): Promise<TripPlan> {
  return postJson<TripPlan>("/trips/plan", request);
}
