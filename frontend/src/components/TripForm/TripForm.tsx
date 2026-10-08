import { useState, type FormEvent } from "react";

import type { TripPlanRequest } from "../../types/trip";
import { departureInputToUtcIso } from "../../utils/formatters";

interface TripFormProps {
  isLoading: boolean;
  onSubmit: (request: TripPlanRequest) => void;
}

interface FormValues {
  current_location: string;
  pickup_location: string;
  dropoff_location: string;
  current_cycle_used_hours: string;
  departure_at: string;
}

type FormErrors = Partial<Record<keyof FormValues, string>>;

const initialValues: FormValues = {
  current_location: "La Plata, Buenos Aires, Argentina",
  pickup_location: "Buenos Aires, Argentina",
  dropoff_location: "Rosario, Santa Fe, Argentina",
  current_cycle_used_hours: "10",
  departure_at: "",
};

export function TripForm({ isLoading, onSubmit }: TripFormProps) {
  const [values, setValues] = useState<FormValues>(initialValues);
  const [errors, setErrors] = useState<FormErrors>({});

  function update(field: keyof FormValues, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validate(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    const departure = values.departure_at ? departureInputToUtcIso(values.departure_at) : undefined;
    onSubmit({
      current_location: values.current_location.trim(),
      pickup_location: values.pickup_location.trim(),
      dropoff_location: values.dropoff_location.trim(),
      current_cycle_used_hours: Number(values.current_cycle_used_hours),
      ...(departure ? { departure_at: departure } : {}),
    });
  }

  return (
    <form className="trip-form" noValidate onSubmit={handleSubmit}>
      <div className="form-intro">
        <p className="eyebrow">Route + HOS planner</p>
        <h1>Build a compliant trip plan</h1>
        <p>Enter the route and current cycle usage. We’ll calculate the route, stops, and duty timeline.</p>
      </div>
      <div className="form-grid">
        <Field
          error={errors.current_location}
          label="Current location"
          name="current_location"
          onChange={update}
          placeholder="City, state, or address"
          value={values.current_location}
        />
        <Field
          error={errors.pickup_location}
          label="Pickup location"
          name="pickup_location"
          onChange={update}
          placeholder="City, state, or address"
          value={values.pickup_location}
        />
        <Field
          error={errors.dropoff_location}
          label="Dropoff location"
          name="dropoff_location"
          onChange={update}
          placeholder="City, state, or address"
          value={values.dropoff_location}
        />
        <Field
          error={errors.current_cycle_used_hours}
          label="Current cycle used (hours)"
          name="current_cycle_used_hours"
          onChange={update}
          placeholder="0–70"
          type="number"
          value={values.current_cycle_used_hours}
        />
        <Field
          error={errors.departure_at}
          label="Departure date and time (UTC)"
          name="departure_at"
          onChange={update}
          type="datetime-local"
          value={values.departure_at}
        />
      </div>
      <p className="timezone-note">All planning times and daily logs are shown in UTC.</p>
      <button className="primary-button" disabled={isLoading} type="submit">
        {isLoading ? "Calculating trip…" : "Calculate trip"}
      </button>
    </form>
  );
}

interface FieldProps {
  error?: string;
  label: string;
  name: keyof FormValues;
  onChange: (field: keyof FormValues, value: string) => void;
  placeholder?: string;
  type?: "text" | "number" | "datetime-local";
  value: string;
}

function Field({ error, label, name, onChange, placeholder, type = "text", value }: FieldProps) {
  const id = `trip-${name}`;
  return (
    <label className="field" htmlFor={id}>
      <span>{label}</span>
      <input
        aria-describedby={error ? `${id}-error` : undefined}
        aria-invalid={Boolean(error)}
        id={id}
        max={name === "current_cycle_used_hours" ? 70 : undefined}
        min={name === "current_cycle_used_hours" ? 0 : undefined}
        name={name}
        onChange={(event) => onChange(name, event.target.value)}
        placeholder={placeholder}
        step={name === "current_cycle_used_hours" ? "0.25" : undefined}
        type={type}
        value={value}
      />
      {error ? <small id={`${id}-error`}>{error}</small> : null}
    </label>
  );
}

function validate(values: FormValues): FormErrors {
  const errors: FormErrors = {};
  for (const field of ["current_location", "pickup_location", "dropoff_location"] as const) {
    if (!values[field].trim()) errors[field] = "This location is required.";
  }
  const cycleHours = Number(values.current_cycle_used_hours);
  if (!values.current_cycle_used_hours || !Number.isFinite(cycleHours) || cycleHours < 0 || cycleHours > 70) {
    errors.current_cycle_used_hours = "Enter a cycle value between 0 and 70 hours.";
  }
  if (values.departure_at && Number.isNaN(new Date(`${values.departure_at}Z`).valueOf())) {
    errors.departure_at = "Enter a valid departure date and time.";
  }
  return errors;
}
