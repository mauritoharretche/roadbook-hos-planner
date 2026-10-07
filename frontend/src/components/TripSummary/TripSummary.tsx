import type { TripPlan } from "../../types/trip";
import { formatDateTime, formatDuration, formatHours, formatMiles } from "../../utils/formatters";

interface TripSummaryProps {
  plan: TripPlan;
}

export function TripSummary({ plan }: TripSummaryProps) {
  const firstEvent = plan.events[0];
  const lastEvent = plan.events.at(-1);
  const isFeasible = plan.status === "feasible";

  return (
    <section className={`summary-card panel ${isFeasible ? "is-feasible" : "is-infeasible"}`}>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Trip summary</p>
          <h2>{isFeasible ? "Plan ready" : "Plan not compliant"}</h2>
        </div>
        <span className="status-pill">{isFeasible ? "Feasible" : "Infeasible"}</span>
      </div>
      {plan.error ? <p className="infeasible-copy">{plan.error.message}</p> : null}
      <dl className="summary-grid">
        <Metric label="Distance" value={formatMiles(plan.summary.total_distance_miles)} />
        <Metric label="Driving" value={formatDuration(plan.summary.total_driving_minutes)} />
        <Metric label="On duty" value={formatDuration(plan.summary.total_on_duty_minutes)} />
        <Metric label="Off duty" value={formatDuration(plan.summary.total_off_duty_minutes)} />
        <Metric label="Cycle used" value={formatHours(plan.summary.cycle_hours_used * 60)} />
        <Metric label="Cycle remaining" value={formatHours(plan.summary.cycle_hours_remaining * 60)} />
        <Metric label="Trip start" value={firstEvent ? formatDateTime(firstEvent.start) : "—"} />
        <Metric label="Trip end" value={lastEvent ? formatDateTime(lastEvent.end) : "—"} />
      </dl>
      {plan.summary.warnings.map((warning) => <p className="warning" key={warning}>{warning}</p>)}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
