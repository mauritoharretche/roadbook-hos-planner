import { useCallback, useState } from "react";

import { ApiError } from "../api/client";
import { planTrip } from "../api/tripApi";
import type { TripPlan, TripPlanRequest } from "../types/trip";

export function useTripPlan() {
  const [plan, setPlan] = useState<TripPlan | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const calculate = useCallback(async (request: TripPlanRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      setPlan(await planTrip(request));
    } catch (caughtError) {
      setPlan(null);
      setError(
        caughtError instanceof ApiError
          ? caughtError.message
          : "Something unexpected happened while calculating the trip.",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { plan, isLoading, error, calculate };
}
