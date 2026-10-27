// My-Field calendar on the phone: fetch a crop's dated tasks (public, cacheable — kept in the
// on-device copy like the forecast) and decide which ones matter today. Pure helpers are tested.

import { useQuery } from "@tanstack/react-query";
import { ApiUnavailable, getJson } from "./api";
import type { components } from "./api.gen";
import type { Crop } from "./types";

export type CalendarOut = components["schemas"]["CalendarOut"];
export type CalendarTask = CalendarOut["tasks"][number];

export async function fetchCalendar(crop: Crop, date: string, signal?: AbortSignal): Promise<CalendarOut> {
  const q = new URLSearchParams({ crop, date });
  const { res, body } = await getJson(`/v1/calendar?${q.toString()}`, signal);
  const b = body as Partial<CalendarOut> | null;
  if (!res.ok || !b || !Array.isArray(b.tasks)) throw new ApiUnavailable(`calendar ${res.status}`);
  return b as CalendarOut;
}

const DAY_MS = 24 * 60 * 60 * 1000;

export function useCalendar(crop: Crop, date: string) {
  return useQuery({
    queryKey: ["calendar", crop, date],
    queryFn: ({ signal }) => fetchCalendar(crop, date, signal),
    staleTime: DAY_MS, // content changes only with a deploy
    gcTime: 7 * DAY_MS,
  });
}

export type TaskWhen = "done" | "now" | "soon" | "later" | "stage";

const SOON_DAYS = 7;

function addDays(iso: string, days: number): string {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

/** Where a task stands on `today` (YYYY-MM-DD in IST). Pure. */
export function taskWhen(t: Pick<CalendarTask, "start" | "end">, today: string): TaskWhen {
  if (t.start === null) return "stage";
  const end = t.end ?? "9999-12-31"; // open-ended: from its start on
  if (end < today) return "done";
  if (t.start <= today) return "now";
  if (t.start <= addDays(today, SOON_DAYS)) return "soon";
  return "later";
}

/** Days from `today` until a date (negative = past). Pure. */
export function daysUntil(date: string, today: string): number {
  return Math.round((Date.parse(`${date}T00:00:00Z`) - Date.parse(`${today}T00:00:00Z`)) / DAY_MS);
}

/** "Due now" and "this week" first, then later, then stage-based; done last. Pure. */
export function ordered(tasks: CalendarTask[], today: string): { task: CalendarTask; when: TaskWhen }[] {
  const rank: Record<TaskWhen, number> = { now: 0, soon: 1, later: 2, stage: 3, done: 4 };
  return tasks
    .map((task) => ({ task, when: taskWhen(task, today) }))
    .sort((a, b) => rank[a.when] - rank[b.when] || (a.task.start ?? "").localeCompare(b.task.start ?? ""));
}
