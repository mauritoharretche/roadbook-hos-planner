import type { TripEvent } from "../../types/trip";
import { eventLabel, formatDateTime, formatDuration } from "../../utils/formatters";

interface StopTimelineProps {
  events: TripEvent[];
}

export function StopTimeline({ events }: StopTimelineProps) {
  const orderedEvents = [...events].sort((left, right) => left.start.localeCompare(right.start));
  return (
    <section className="timeline-card panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Duty timeline</p>
          <h2>Trip events</h2>
        </div>
        <span className="event-count">{orderedEvents.length} events</span>
      </div>
      <ol className="timeline">
        {orderedEvents.map((event, index) => (
          <li className={`timeline-item type-${event.event_type.toLowerCase()}`} key={`${event.start}-${event.event_type}-${index}`}>
            <div className="timeline-marker" aria-hidden="true" />
            <div className="timeline-content">
              <div className="timeline-title-row">
                <h3>{eventLabel(event.event_type)}</h3>
                <strong>{formatDuration(event.duration_minutes)}</strong>
              </div>
              <p>{formatDateTime(event.start)} — {formatDateTime(event.end)}</p>
              {event.segment_name ? <p className="location">{event.segment_name}</p> : null}
              <p className="reason">{event.reason}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
