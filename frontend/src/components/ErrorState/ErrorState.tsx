interface ErrorStateProps {
  message: string;
}

export function ErrorState({ message }: ErrorStateProps) {
  return (
    <div className="state-card error-state" role="alert">
      <div className="state-icon">!</div>
      <div>
        <h2>We couldn’t calculate this trip</h2>
        <p>{message}</p>
      </div>
    </div>
  );
}
