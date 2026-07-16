import { describe, expect, it } from "vitest";
import { friendlyError, isValidEmail, passwordProblem } from "./auth";

describe("isValidEmail", () => {
  it("accepts normal emails", () => {
    expect(isValidEmail("ravi@example.com")).toBe(true);
    expect(isValidEmail(" ravi@farm.co.in ")).toBe(true);
  });
  it("rejects malformed", () => {
    for (const bad of ["", "ravi", "ravi@", "@x.com", "a b@x.com", "ravi@x"]) {
      expect(isValidEmail(bad), bad).toBe(false);
    }
  });
});

describe("passwordProblem (mirrors the Cognito pool policy)", () => {
  it("passes an 8+ char password with a letter and a digit", () => {
    expect(passwordProblem("rythu2026")).toBeNull();
  });
  it("flags too short / missing lowercase / missing digit", () => {
    expect(passwordProblem("ry26")).toContain("8");
    expect(passwordProblem("12345678")).toContain("a-z");
    expect(passwordProblem("password")).toContain("0-9");
  });
});

describe("friendlyError", () => {
  it("maps known Cognito codes to friendly text", () => {
    expect(friendlyError({ name: "UsernameExistsException" })).toContain("already");
    expect(friendlyError({ name: "NotAuthorizedException" })).toContain("Wrong");
    expect(friendlyError({ code: "CodeMismatchException" })).toContain("Wrong code");
  });
  it("falls back to the message then a generic line", () => {
    expect(friendlyError({ message: "boom" })).toBe("boom");
    expect(friendlyError({})).toContain("Something went wrong");
  });
});
