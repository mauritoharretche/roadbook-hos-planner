import { DailyLogTabs } from "../components/DailyLogTabs/DailyLogTabs";
import { ErrorState } from "../components/ErrorState/ErrorState";
import { LoadingState } from "../components/LoadingState/LoadingState";
import { RouteMap } from "../components/RouteMap/RouteMap";
import { StopTimeline } from "../components/StopTimeline/StopTimeline";
import { TripForm } from "../components/TripForm/TripForm";
import { TripSummary } from "../components/TripSummary/TripSummary";
import { useTripPlan } from "../hooks/useTripPlan";
import type { TripPlan } from "../types/trip";

export function PlannerPage() {
  const { plan, isLoading, error, calculate } = useTripPlan();

  return (
    <main className="page-shell">
      <header className="site-header">
        <a className="brand" href="#planner"><span>R</span> Roadbook</a>
        <p>Property-carrying driver · HOS trip planning</p>
      </header>
      <div className="planner-stack" id="planner">
        <TripForm isLoading={isLoading} onSubmit={calculate} />
        {isLoading ? <LoadingState /> : null}
        {error ? <ErrorState message={error} /> : null}
        {plan ? <PlanContent plan={plan} /> : <EmptyState />}
      </div>
    </main>
  );
}

function PlanContent({ plan }: { plan: TripPlan }) {
  return (
    <section className="results" aria-live="polite">
      {plan.status === "infeasible" ? <ErrorState message={plan.error?.message ?? "This trip is not HOS compliant."} /> : null}
      <div className="route-summary-grid">
        <RouteMap route={plan.route} />
        <TripSummary plan={plan} />
      </div>
      <StopTimeline events={plan.events} />
      <DailyLogTabs dailyLogs={plan.daily_logs} />
    </section>
  );
}

function EmptyState() {
  return (
    <section className="state-card empty-state">
      <div className="state-icon">↗</div>
      <div>
        <h2>Plan a trip to see route and HOS information.</h2>
        <p>Your route, required duty events, cycle capacity, and daily log summaries will appear here.</p>
      </div>
    </section>
  );
}
