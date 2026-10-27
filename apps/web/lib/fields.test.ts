import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { TRANSPLANTED, newFieldId, parseFields } from "./fields";
import { daysUntil, ordered, taskWhen, type CalendarTask } from "./calendar";

describe("fields", () => {
  it("counts from transplanting for exactly the crops the backend calendar does", () => {
    const py = readFileSync(
      new URL("../../../services/weather/src/rythu_weather/domain/calendar.py", import.meta.url),
      "utf8",
    );
    const backend = [...py.matchAll(/Crop\.([A-Z_]+): CropCalendar\(Reference\.TRANSPLANTING/g)].map((m) =>
      m[1]!.toLowerCase(),
    );
    expect(new Set(backend)).toEqual(new Set(TRANSPLANTED));
  });

  it("makes ids the API accepts", () => {
    for (let i = 0; i < 50; i++) expect(newFieldId()).toMatch(/^[a-z0-9]{6,16}$/);
  });

  it("ignores junk in storage and keeps at most five", () => {
    const ok = { id: "abcdef", name: "East", crop: "paddy", reference_date: "2026-07-01" };
    expect(parseFields("not json")).toEqual([]);
    expect(parseFields(JSON.stringify([ok, { id: "X" }, null]))).toEqual([ok]);
    expect(parseFields(JSON.stringify(Array.from({ length: 8 }, (_, i) => ({ ...ok, id: `abcde${i}` }))))).toHaveLength(5);
  });
});

describe("calendar timing", () => {
  const task = (start: string | null, end: string | null) => ({ start, end }) as CalendarTask;
  const TODAY = "2026-10-27";

  it("places a task relative to today", () => {
    expect(taskWhen(task("2026-10-01", "2026-10-01"), TODAY)).toBe("done");
    expect(taskWhen(task("2026-10-27", "2026-10-27"), TODAY)).toBe("now");
    expect(taskWhen(task("2026-10-20", "2026-10-30"), TODAY)).toBe("now"); // in its window
    expect(taskWhen(task("2026-09-01", null), TODAY)).toBe("now"); // open-ended: from then on
    expect(taskWhen(task("2026-11-03", "2026-11-03"), TODAY)).toBe("soon"); // within a week
    expect(taskWhen(task("2026-11-04", "2026-11-04"), TODAY)).toBe("later");
    expect(taskWhen(task(null, null), TODAY)).toBe("stage");
  });

  it("orders what matters now first and finished work last", () => {
    const list = [task("2026-10-01", "2026-10-01"), task(null, null), task("2026-12-01", "2026-12-01"), task("2026-10-30", "2026-10-30"), task("2026-10-27", "2026-10-27")];
    expect(ordered(list, TODAY).map((x) => x.when)).toEqual(["now", "soon", "later", "stage", "done"]);
    expect(daysUntil("2026-10-30", TODAY)).toBe(3);
    expect(daysUntil("2026-10-20", TODAY)).toBe(-7);
  });
});
