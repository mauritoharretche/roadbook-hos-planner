# Roadbook Loom script (3–5 minutes)

## 0:00–0:30 — Problem and solution

“Roadbook plans a property-carrying trip from a current location through pickup
and dropoff. It combines route distance with the required HOS constraints and
returns an auditable timeline and daily duty logs.”

## 0:30–1:30 — Enter and calculate a trip

Use the demo route:

- Current: Los Angeles, CA
- Pickup: Dallas, TX
- Dropoff: New Orleans, LA
- Current Cycle Used: 10 hours

Click **Calculate trip**. Point out the required inputs and the optional
departure time.

## 1:30–2:30 — Map, summary, and timeline

Show the map markers and route. Highlight total distance, driving/on-duty time,
cycle remaining, pickup, dropoff, planned fuel, the required 30-minute break,
and 10-hour rest periods in the chronological timeline. Explain that fuel stops
are distance-based planning markers, not verified named fuel stations.

## 2:30–3:30 — Daily logs

Open the daily-log tabs. Show the complete 24-hour SVG grid, status transitions,
and remarks. Explain that empty portions of a day are rendered as off duty for
visual completeness only; backend events and calculations are preserved.

## 3:30–4:30 — Architecture

Show the small architecture diagram in the README. Explain that React only
displays API results, Django adapts providers, and the HOS planner is pure
Python with no Django imports. Mention the swappable mock/ORS provider.

## 4:30–5:00 — Summary

“The app deliberately scopes out authentication, persistence, and certified
ELD claims. It focuses the assessment time on testable HOS calculations, a
clear user flow, real routing readiness, and an inspectable daily-log view.”
