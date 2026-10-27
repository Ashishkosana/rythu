// Ask Rythu (S17): send a farmer's question to the API, which answers only from Rythu's own checked
// content. Every outcome maps to something the screen can say honestly — and every one of them
// offers the free Kisan Call Centre, a human who can always help.

import { ApiUnavailable } from "./api";
import { NoDevice, authedFetch } from "./device";
import type { AskIn, AskOut, Crop, WaterSource } from "./types";

export const MIN_QUESTION = 3;
export const MAX_QUESTION = 300;
// The server allows the model 25 s with one retry; the phone waits a little longer than that.
export const ASK_TIMEOUT_MS = 60_000;

export type AskResult =
  | { kind: "answer"; out: AskOut }
  | { kind: "limit" } // today's questions are used up (this phone, or everyone)
  | { kind: "off" } // switched off on the server
  | { kind: "unavailable" } // server or model trouble: try again
  | { kind: "offline" }; // no internet

export interface AskContext {
  lat?: number;
  lon?: number;
  crop?: Crop | null;
  water?: WaterSource | null;
}

export function askBody(question: string, lang: "te" | "en", ctx: AskContext): AskIn {
  const body: AskIn = { question: question.trim().slice(0, MAX_QUESTION), lang, water: ctx.water ?? "rainfed" };
  if (typeof ctx.lat === "number" && typeof ctx.lon === "number") {
    body.lat = ctx.lat;
    body.lon = ctx.lon;
  }
  if (ctx.crop) body.crop = ctx.crop;
  return body;
}

export function canAsk(question: string): boolean {
  const q = question.trim();
  return q.length >= MIN_QUESTION && q.length <= MAX_QUESTION;
}

export async function askRythu(question: string, lang: "te" | "en", ctx: AskContext): Promise<AskResult> {
  if (typeof navigator !== "undefined" && navigator.onLine === false) return { kind: "offline" };
  let res: Response;
  try {
    res = await authedFetch(
      "/v1/assistant/ask",
      { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(askBody(question, lang, ctx)) },
      { create: true, timeoutMs: ASK_TIMEOUT_MS },
    );
  } catch (err) {
    if (err instanceof ApiUnavailable || err instanceof NoDevice) return { kind: "unavailable" };
    throw err;
  }
  if (res.ok) return { kind: "answer", out: (await res.json()) as AskOut };
  if (res.status === 429) return { kind: "limit" };
  const code = ((await res.json().catch(() => null)) as { code?: string } | null)?.code;
  if (res.status === 503 && code === "assistant_off") return { kind: "off" };
  return { kind: "unavailable" };
}
