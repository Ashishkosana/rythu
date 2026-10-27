import { describe, expect, it } from "vitest";
import { CYBER_CRIME, KISAN_CALL_CENTRE } from "./helplines";

describe("helplines", () => {
  it("dial exactly the number they show", () => {
    for (const h of [KISAN_CALL_CENTRE, CYBER_CRIME]) {
      expect(h.tel).toBe(`tel:${h.display.replace(/-/g, "")}`);
      expect(h.source).toMatch(/^https:\/\/[^/]+\.gov\.in/);
    }
  });
});
