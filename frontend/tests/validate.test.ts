import { describe, expect, it } from "vitest";
import { validateTripForm } from "../lib/validate";

describe("validateTripForm", () => {
  it("should pass a valid form", () => {
    const errors = validateTripForm({
      destination: "Jaipur",
      number_of_days: 3,
      budget: 30000,
      interests: ["History", "Architecture"],
    });
    expect(errors).toEqual({});
  });

  it("should reject an empty destination", () => {
    const errors = validateTripForm({
      destination: "   ",
      number_of_days: 3,
      budget: 30000,
      interests: ["History"],
    });
    expect(errors.destination).toBeDefined();
  });

  it("should reject zero or negative days", () => {
    expect(
      validateTripForm({
        destination: "Jaipur",
        number_of_days: 0,
        budget: 100,
        interests: ["History"],
      }).number_of_days,
    ).toBeDefined();

    expect(
      validateTripForm({
        destination: "Jaipur",
        number_of_days: -2,
        budget: 100,
        interests: ["History"],
      }).number_of_days,
    ).toBeDefined();
  });

  it("should reject fractional days", () => {
    const errors = validateTripForm({
      destination: "Jaipur",
      number_of_days: 2.5,
      budget: 100,
      interests: ["History"],
    });
    expect(errors.number_of_days).toBeDefined();
  });

  it("should reject a non-positive budget", () => {
    expect(
      validateTripForm({
        destination: "Jaipur",
        number_of_days: 3,
        budget: 0,
        interests: ["History"],
      }).budget,
    ).toBeDefined();

    expect(
      validateTripForm({
        destination: "Jaipur",
        number_of_days: 3,
        budget: -500,
        interests: ["History"],
      }).budget,
    ).toBeDefined();
  });

  it("should require at least one interest", () => {
    const errors = validateTripForm({
      destination: "Jaipur",
      number_of_days: 3,
      budget: 30000,
      interests: [],
    });
    expect(errors.interests).toBeDefined();
  });

  it("should collect multiple errors at once", () => {
    const errors = validateTripForm({
      destination: "",
      number_of_days: 0,
      budget: 0,
      interests: [],
    });
    expect(errors.destination).toBeDefined();
    expect(errors.number_of_days).toBeDefined();
    expect(errors.budget).toBeDefined();
    expect(errors.interests).toBeDefined();
  });
});