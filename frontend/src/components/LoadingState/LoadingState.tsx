export function LoadingState() {
  return (
    <div aria-live="polite" className="state-card loading-state">
      <span className="spinner" aria-hidden="true" />
      <div>
        <h2>Calculating route and HOS plan…</h2>
        <p>Checking driving limits, duty time, required stops, and daily logs.</p>
      </div>
    </div>
  );
}
