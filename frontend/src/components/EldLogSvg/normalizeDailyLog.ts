import type { DailyLog, DutyStatus, TripEvent } from "../../types/trip";

export interface EldInterval {
  dutyStatus: DutyStatus;
  endMinute: number;
  event?: TripEvent;
  isGap: boolean;
  startMinute: number;
}

const DAY_MINUTES = 24 * 60;

export function normalizeDailyLog(dailyLog: DailyLog): EldInterval[] {
  const intervals: EldInterval[] = [];
  const events = [...dailyLog.events].sort((left, right) => left.start.localeCompare(right.start));
  let cursor = 0;

  for (const event of events) {
    const startMinute = clamp(minuteForDay(dailyLog.date, event.start));
    const endMinute = clamp(minuteForDay(dailyLog.date, event.end));
    if (endMinute <= cursor || endMinute <= startMinute) continue;
    if (startMinute > cursor) intervals.push(gap(cursor, startMinute));
    intervals.push({
      dutyStatus: event.duty_status,
      endMinute,
      event,
      isGap: false,
      startMinute: Math.max(startMinute, cursor),
    });
    cursor = endMinute;
  }

  if (cursor < DAY_MINUTES) intervals.push(gap(cursor, DAY_MINUTES));
  return intervals.length ? intervals : [gap(0, DAY_MINUTES)];
}

function gap(startMinute: number, endMinute: number): EldInterval {
  return { dutyStatus: "OFF_DUTY", startMinute, endMinute, isGap: true };
}

function minuteForDay(day: string, eventTime: string): number {
  const midnight = Date.parse(`${day}T00:00:00Z`);
  return (Date.parse(eventTime) - midnight) / 60_000;
}

function clamp(minutes: number): number {
  return Math.max(0, Math.min(DAY_MINUTES, minutes));
}
