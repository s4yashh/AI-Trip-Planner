export interface TripFormValues {
  destination: string;
  number_of_days: number;
  budget: number;
  interests: string[];
  start_date?: string;
}

export interface TripFormErrors {
  destination?: string;
  number_of_days?: string;
  budget?: string;
  interests?: string;
  start_date?: string;
}

export function validateTripForm(values: TripFormValues): TripFormErrors {
  const errors: TripFormErrors = {};

  if (!values.destination.trim()) {
    errors.destination = "Please enter a destination.";
  }

  if (!Number.isInteger(values.number_of_days) || values.number_of_days <= 0) {
    errors.number_of_days = "Number of days must be a whole number greater than 0.";
  }

  if (
    typeof values.budget !== "number" ||
    Number.isNaN(values.budget) ||
    values.budget <= 0
  ) {
    errors.budget = "Budget must be greater than 0.";
  }

  if (!values.interests || values.interests.length === 0) {
    errors.interests = "Select at least one interest.";
  }

  if (values.start_date && !/^\d{4}-\d{2}-\d{2}$/.test(values.start_date)) {
    errors.start_date = "Start date must be a valid YYYY-MM-DD date.";
  }

  return errors;
}