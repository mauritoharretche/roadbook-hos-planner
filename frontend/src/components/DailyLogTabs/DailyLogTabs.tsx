import { useState } from "react";

import type { DailyLog } from "../../types/trip";
import { EldLogSvg } from "../EldLogSvg/EldLogSvg";
import { eventLabel, formatDate, formatDateTime, formatDuration, formatHours } from "../../utils/formatters";

interface DailyLogTabsProps {
  dailyLogs: DailyLog[];
}

export function DailyLogTabs({ dailyLogs }: DailyLogTabsProps) {
  const [selectedDate, setSelectedDate] = useState(dailyLogs[0]?.date ?? "");
  const selectedLog = dailyLogs.find((dailyLog) => dailyLog.date === selectedDate) ?? dailyLogs[0];
  if (!selectedLog) return null;

  return (
    <section className="daily-logs-card panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Daily logs</p>
          <h2>Duty status by day</h2>
          <p className="timezone-note">All times are shown in UTC.</p>
        </div>
        <span className="event-count">{dailyLogs.length} day{dailyLogs.length === 1 ? "" : "s"}</span>
      </div>
      <div aria-label="Daily log dates" className="log-tabs" role="tablist">
        {dailyLogs.map((dailyLog, index) => (
          <button
            aria-selected={dailyLog.date === selectedLog.date}
            className={dailyLog.date === selectedLog.date ? "active" : ""}
            key={dailyLog.date}
            onClick={() => setSelectedDate(dailyLog.date)}
            role="tab"
            type="button"
          >
            <strong>Day {index + 1}</strong>
            <small>{formatDate(dailyLog.date)}</small>
          </button>
        ))}
      </div>
      <div className="daily-log-content" role="tabpanel">
        <dl className="daily-stats">
          <Metric label="Driving" value={formatHours(selectedLog.driving_minutes)} />
          <Metric label="On duty" value={formatHours(selectedLog.on_duty_not_driving_minutes)} />
          <Metric label="Off duty" value={formatHours(selectedLog.off_duty_minutes)} />
          <Metric label="Total logged" value={formatHours(selectedLog.total_minutes)} />
          <Metric label="Events" value={String(selectedLog.events.length)} />
        </dl>
        <EldLogSvg dailyLog={selectedLog} />
        <ul className="daily-event-list">
          {selectedLog.events.map((event, index) => (
            <li key={`${event.start}-${index}`}>
              <strong>{eventLabel(event.event_type)}</strong>
              <span>{formatDateTime(event.start)} · {formatDuration(event.duration_minutes)}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div><dt>{label}</dt><dd>{value}</dd></div>;
}
