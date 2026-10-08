import type { DailyLog, DutyStatus } from "../../types/trip";
import { eventLabel, formatDate, formatHours } from "../../utils/formatters";
import { normalizeDailyLog } from "./normalizeDailyLog";

interface EldLogSvgProps {
  dailyLog: DailyLog;
}

const plot = { left: 190, top: 82, width: 1215, rowHeight: 44 };
const rows: { label: string; status: DutyStatus }[] = [
  { label: "OFF DUTY", status: "OFF_DUTY" },
  { label: "SLEEPER BERTH", status: "SLEEPER_BERTH" },
  { label: "DRIVING", status: "DRIVING" },
  { label: "ON DUTY", status: "ON_DUTY_NOT_DRIVING" },
];
const colors: Record<DutyStatus, string> = {
  OFF_DUTY: "#587087",
  SLEEPER_BERTH: "#7255a4",
  DRIVING: "#215b8d",
  ON_DUTY_NOT_DRIVING: "#cc7a00",
};

export function EldLogSvg({ dailyLog }: EldLogSvgProps) {
  const intervals = normalizeDailyLog(dailyLog);
  const rowCenter = (status: DutyStatus) => plot.top + rows.findIndex((row) => row.status === status) * plot.rowHeight + plot.rowHeight / 2;
  const xForMinute = (minutes: number) => plot.left + (minutes / 1440) * plot.width;
  const remarks = dailyLog.events.filter((event) => event.event_type !== "DRIVING");

  return (
    <div className="eld-log" data-testid="eld-log">
      <div className="eld-scroll">
        <svg aria-label={`24-hour UTC duty status log for ${dailyLog.date}`} className="eld-svg" role="img" viewBox="0 0 1440 360">
          <title>{`Daily duty status log for ${formatDate(dailyLog.date)} (UTC)`}</title>
          <desc>A 24-hour planning visualization. Unplanned gaps are displayed as off duty.</desc>
          <rect fill="#fbfdff" height="360" rx="10" width="1440" x="0" y="0" />
          <text className="eld-title" x="28" y="32">DAILY DRIVER LOG · PLANNING VIEW (UTC)</text>
          <text className="eld-date" x="28" y="56">{formatDate(dailyLog.date)} · UTC</text>
          <text className="eld-total" x="720" y="32">Driving {formatHours(dailyLog.driving_minutes)}</text>
          <text className="eld-total" x="970" y="32">On duty {formatHours(dailyLog.on_duty_not_driving_minutes)}</text>
          <text className="eld-total" x="1190" y="32">Off duty {formatHours(dailyLog.off_duty_minutes)}</text>
          {Array.from({ length: 25 }, (_, hour) => {
            const x = xForMinute(hour * 60);
            return <g key={hour}>
              <line className={hour % 6 === 0 ? "eld-grid-major" : "eld-grid"} x1={x} x2={x} y1={plot.top} y2={plot.top + plot.rowHeight * 4} />
              {hour < 24 ? <text className="eld-hour" textAnchor="middle" x={x} y={plot.top - 10}>{hour === 0 ? "M" : hour === 12 ? "N" : hour > 12 ? hour - 12 : hour}</text> : null}
            </g>;
          })}
          {rows.map((row, index) => {
            const y = plot.top + index * plot.rowHeight;
            return <g key={row.status}>
              <text className="eld-row-label" textAnchor="end" x={plot.left - 14} y={y + plot.rowHeight / 2 + 4}>{row.label}</text>
              <line className="eld-grid-major" x1={plot.left} x2={plot.left + plot.width} y1={y} y2={y} />
            </g>;
          })}
          <line className="eld-grid-major" x1={plot.left} x2={plot.left + plot.width} y1={plot.top + plot.rowHeight * 4} y2={plot.top + plot.rowHeight * 4} />
          {intervals.map((interval, index) => (
            <line
              data-end-minute={interval.endMinute}
              data-start-minute={interval.startMinute}
              data-status={interval.dutyStatus}
              data-testid="duty-segment"
              key={`${interval.startMinute}-${interval.endMinute}-${index}`}
              stroke={colors[interval.dutyStatus]}
              strokeLinecap="round"
              strokeWidth="5"
              x1={xForMinute(interval.startMinute)}
              x2={xForMinute(interval.endMinute)}
              y1={rowCenter(interval.dutyStatus)}
              y2={rowCenter(interval.dutyStatus)}
            />
          ))}
          {intervals.slice(1).map((interval, index) => {
            const previous = intervals[index];
            if (previous.dutyStatus === interval.dutyStatus) return null;
            const x = xForMinute(interval.startMinute);
            return <line data-testid="duty-transition" key={`transition-${index}`} stroke="#334e68" strokeWidth="2" x1={x} x2={x} y1={rowCenter(previous.dutyStatus)} y2={rowCenter(interval.dutyStatus)} />;
          })}
          <text className="eld-axis-label" x={plot.left} y="288">MIDNIGHT UTC</text>
          <text className="eld-axis-label" textAnchor="end" x={plot.left + plot.width} y="288">MIDNIGHT UTC</text>
        </svg>
      </div>
      <div className="eld-remarks">
        <strong>Remarks</strong>
        {remarks.length ? (
          <ul>
            {remarks.map((event, index) => <li key={`${event.start}-${index}`}>{eventLabel(event.event_type)} — {event.segment_name ?? event.reason}</li>)}
          </ul>
        ) : <span>No non-driving trip events recorded for this day.</span>}
        <small>Planning visualization only; not a certified ELD record.</small>
      </div>
    </div>
  );
}
