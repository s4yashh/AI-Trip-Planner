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

interface TripFormProps {
  onSubmit: (payload: TripFormPayload) => void;
  disabled?: boolean;
}

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

  const inputClass = (hasError: boolean) =>
    `w-full rounded-lg border bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:outline-none focus:ring-2 ${
      hasError
        ? "border-red-400 focus:ring-red-300"
        : "border-slate-300 focus:border-emerald-500 focus:ring-emerald-200"
    }`;

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5">
      <div>
        <label htmlFor="destination" className="mb-1.5 block text-sm font-medium text-slate-700">
          Where do you want to go?
        </label>
        <input
          id="destination"
          name="destination"
          type="text"
          value={destination}
          onChange={(event) => setDestination(event.target.value)}
          placeholder="e.g. Jaipur, Paris, Tokyo"
          className={inputClass(Boolean(errors.destination))}
        />
        {errors.destination ? (
          <p className="mt-1.5 text-sm text-red-600" role="alert">
            {errors.destination}
          </p>
        ) : null}
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <div>
          <label htmlFor="days" className="mb-1.5 block text-sm font-medium text-slate-700">
            Number of Days
          </label>
          <input
            id="days"
            name="number_of_days"
            type="number"
            min={1}
            max={60}
            inputMode="numeric"
            value={days}
            onChange={(event) => setDays(Number(event.target.value))}
            className={inputClass(Boolean(errors.number_of_days))}
          />
          {errors.number_of_days ? (
            <p className="mt-1.5 text-sm text-red-600" role="alert">
              {errors.number_of_days}
            </p>
          ) : null}
        </div>

        <div>
          <label htmlFor="budget" className="mb-1.5 block text-sm font-medium text-slate-700">
            Budget
          </label>
          <div className="flex">
            <span className="inline-flex items-center rounded-l-lg border border-r-0 border-slate-300 bg-slate-50 px-3 text-sm text-slate-600">
              {currency === "INR" ? "\u20b9" : "$"}
            </span>
            <input
              id="budget"
              name="budget"
              type="number"
              min={1}
              inputMode="numeric"
              value={budget}
              onChange={(event) => setBudget(Number(event.target.value))}
              className={`${inputClass(Boolean(errors.budget))} rounded-l-none`}
            />
          </div>
          {errors.budget ? (
            <p className="mt-1.5 text-sm text-red-600" role="alert">
              {errors.budget}
            </p>
          ) : null}
        </div>
      </div>

      <div className="flex items-center gap-2 text-sm text-slate-600">
        <span>Currency:</span>
        {(["INR", "USD"] as const).map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => setCurrency(option)}
            aria-pressed={currency === option}
            className={`rounded px-2 py-0.5 text-xs font-semibold ${
              currency === option
                ? "bg-slate-900 text-white"
                : "border border-slate-300 text-slate-600 hover:border-slate-400"
            }`}
          >
            {option}
          </button>
        ))}
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

      <div className="pt-2">
        <button
          type="submit"
          disabled={disabled}
          className="w-full rounded-lg bg-emerald-600 px-5 py-3 text-base font-semibold text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
        >
          Generate My Trip
        </button>
      </div>
    </form>
  );
}