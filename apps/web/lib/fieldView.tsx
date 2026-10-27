"use client";

// Small pieces shared by the "My field" screen and the home screen's "this week" card. Kept out of
// components/FieldScreen.tsx so the home page does not bundle the whole field screen.

import { useSyncExternalStore } from "react";
import { daysUntil, type CalendarTask, type TaskWhen } from "./calendar";
import { loadFieldsRaw, parseFields, type MyField } from "./fields";
import { localDate } from "./freshness";
import { pick, type Lang } from "./lang";
import { PREFS_EVENT } from "./prefs";
import { useNow } from "./useNow";

function subscribe(cb: () => void) {
  window.addEventListener(PREFS_EVENT, cb);
  window.addEventListener("storage", cb);
  return () => {
    window.removeEventListener(PREFS_EVENT, cb);
    window.removeEventListener("storage", cb);
  };
}

export function useFields(): MyField[] {
  return parseFields(useSyncExternalStore(subscribe, loadFieldsRaw, () => null));
}

export function useToday(): string {
  return localDate(useNow(), "Asia/Kolkata");
}

export function formatDay(iso: string, lang: Lang): string {
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString(lang === "te" ? "te-IN" : "en-IN", {
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  });
}

export function whenText(task: CalendarTask, when: TaskWhen, today: string, lang: Lang): string {
  if (task.start === null) return pick(lang, task.stage_te ?? "", task.stage_en ?? "");
  const start = formatDay(task.start, lang);
  if (task.end === null) return pick(lang, `${start} నుండి`, `from ${start}`);
  const range = task.end === task.start ? start : `${start} – ${formatDay(task.end, lang)}`;
  if (when === "soon") {
    const d = daysUntil(task.start, today);
    return `${range} · ${pick(lang, `${d} రోజుల్లో`, `in ${d} day${d === 1 ? "" : "s"}`)}`;
  }
  return range;
}
