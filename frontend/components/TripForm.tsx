"use client";

import { useState, type FormEvent } from "react";
import { InterestSelector } from "./InterestSelector";
import { validateTripForm, type TripFormErrors, type TripFormValues } from "@/lib/validate";
import type { Currency, Interest } from "@/types/trip";

export interface TripFormPayload {
  destination: string;
  number_of_days: number;
  budget: number;
  interests: string[];
  currency: Currency;
}

function FieldMessage({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="mt-1.5 pl-1 text-sm text-red-600" role="alert">{message}</p>;
}

interface TripFormProps {
  onSubmit: (payload: TripFormPayload) => void;
  disabled?: boolean;
}

const FIELD_ICONS = {
  destination: (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 21s-7-5.1-7-11a7 7 0 0 1 14 0c0 5.9-7 11-7 11z" />
      <circle cx="12" cy="10" r="2.5" />
    </svg>
  ),
  days: (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M8 3v4M16 3v4M3 9h18" />
    </svg>
  ),
  budget: (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="2" y="6" width="20" height="12" rx="2" />
      <circle cx="12" cy="12" r="2.5" />
    </svg>
  ),
};

export function TripForm({ onSubmit, disabled = false }: TripFormProps) {
  const [destination, setDestination] = useState("");
  const [days, setDays] = useState(3);
  const [budget, setBudget] = useState(30000);
  const [interests, setInterests] = useState<Interest[]>([
    "History",
    "Architecture",
    "Culture",
  ]);
  const [currency, setCurrency] = useState<Currency>("INR");
  const [errors, setErrors] = useState<TripFormErrors>({});

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const values: TripFormValues = {
      destination: destination.trim(),
      number_of_days: days,
      budget,
      interests,
    };
    const validation = validateTripForm(values);
    setErrors(validation);
    if (Object.keys(validation).length > 0) {
      return;
    }
    onSubmit({ ...values, currency });
  }

  function fieldClass(hasError: boolean) {
    return `w-full rounded-xl border bg-white py-2.5 pl-10 pr-3 text-sm text-slate-900 shadow-sm transition-colors focus:outline-none focus:ring-4 ${
      hasError
        ? "border-red-300 focus:border-red-400 focus:ring-red-100"
        : "border-slate-200 focus:border-emerald-500 focus:ring-emerald-100"
    }`;
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-6">
      <div>
        <label htmlFor="destination" className="mb-2 block text-sm font-semibold text-slate-700">
          Where do you want to go?
        </label>
        <div className="relative">
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
            {FIELD_ICONS.destination}
          </span>
          <input
            id="destination"
            name="destination"
            type="text"
            value={destination}
            onChange={(event) => setDestination(event.target.value)}
            placeholder="e.g. Jaipur, Paris, Tokyo"
            className={fieldClass(Boolean(errors.destination))}
          />
        </div>
        <FieldMessage message={errors.destination} />
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <div>
          <label htmlFor="days" className="mb-2 block text-sm font-semibold text-slate-700">
            Number of Days
          </label>
          <div className="relative">
            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
              {FIELD_ICONS.days}
            </span>
            <input
              id="days"
              name="number_of_days"
              type="number"
              min={1}
              max={60}
              inputMode="numeric"
              value={days}
              onChange={(event) => setDays(Number(event.target.value))}
              className={fieldClass(Boolean(errors.number_of_days))}
            />
          </div>
          <FieldMessage message={errors.number_of_days} />
        </div>

        <div>
          <label htmlFor="budget" className="mb-2 block text-sm font-semibold text-slate-700">
            Budget
          </label>
          <div className="relative">
            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
              {FIELD_ICONS.budget}
            </span>
            <input
              id="budget"
              name="budget"
              type="number"
              min={1}
              inputMode="numeric"
              value={budget}
              onChange={(event) => setBudget(Number(event.target.value))}
              className={fieldClass(Boolean(errors.budget))}
            />
            <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm font-semibold text-slate-400">
              {currency === "INR" ? "INR" : "USD"}
            </span>
          </div>
          <FieldMessage message={errors.budget} />
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-slate-50 p-2">
        <p className="px-2 pt-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Currency
        </p>
        <div className="mt-2 grid grid-cols-2 gap-1 rounded-lg bg-white p-1 shadow-inner">
          {(["INR", "USD"] as const).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setCurrency(option)}
              aria-pressed={currency === option}
              className={`rounded-md px-3 py-1.5 text-sm font-semibold transition-all ${
                currency === option
                  ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {option === "INR" ? "₹ INR" : "$ USD"}
            </button>
          ))}
        </div>
      </div>

      <InterestSelector
        selected={interests}
        onChange={(value) => {
          setInterests(value);
          if (value.length > 0 && errors.interests) {
            setErrors((previous) => ({ ...previous, interests: undefined }));
          }
        }}
        error={errors.interests}
      />

      <button
        type="submit"
        disabled={disabled}
        className="group flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-3.5 text-base font-semibold text-white shadow-lg shadow-emerald-600/25 transition-all hover:shadow-xl hover:shadow-emerald-600/35 hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <svg viewBox="0 0 24 24" className="h-5 w-5 transition-transform group-hover:scale-110" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="m3 11 18-7-7 18-2.5-7.5L3 11z" />
        </svg>
        Generate My Trip
      </button>
    </form>
  );
}