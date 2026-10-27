// Speak a question instead of typing it (Ask Rythu, S17). Uses the phone's own speech recognition:
// in Chrome on Android, Google's speech service turns the audio into text (the privacy page says so).
// Feature-detected — where it isn't available, the mic button simply isn't shown.

interface RecognitionEvent {
  results: ArrayLike<ArrayLike<{ transcript: string }>>;
}

interface Recognition {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  continuous: boolean;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((e: RecognitionEvent) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
}

type RecognitionCtor = new () => Recognition;

function ctor(): RecognitionCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as { SpeechRecognition?: RecognitionCtor; webkitSpeechRecognition?: RecognitionCtor };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export function recognitionSupported(): boolean {
  return ctor() !== null;
}

export type Heard =
  | { kind: "text"; text: string }
  | { kind: "nothing" } // silence, or stopped before any words
  | { kind: "blocked" } // microphone permission refused
  | { kind: "failed" }; // no network for the speech service, or anything else

export const MAX_LISTEN_MS = 15_000;
const GRACE_MS = 1_000;

/** Listen once. `stop()` ends early and keeps what was heard. Never hangs: after MAX_LISTEN_MS, or
 *  GRACE_MS after a stop the recogniser doesn't answer, it settles with whatever it has. */
export function listen(lang: "te" | "en"): { result: Promise<Heard>; stop: () => void } {
  const Ctor = ctor();
  if (!Ctor) return { result: Promise.resolve({ kind: "failed" }), stop: () => {} };
  const rec = new Ctor();
  rec.lang = lang === "te" ? "te-IN" : "en-IN";
  rec.interimResults = false;
  rec.maxAlternatives = 1;
  rec.continuous = false;
  let heard: Heard = { kind: "nothing" };
  let settle: () => void = () => {};
  const timers: ReturnType<typeof setTimeout>[] = [];
  const result = new Promise<Heard>((resolve) => {
    settle = () => {
      timers.forEach(clearTimeout);
      resolve(heard);
    };
  });
  const stop = () => {
    try {
      rec.stop();
    } catch {
      /* already stopped */
    }
    timers.push(setTimeout(settle, GRACE_MS));
  };
  rec.onresult = (e) => {
    const text = Array.from(e.results, (r) => r[0]?.transcript ?? "").join(" ").trim();
    if (text) heard = { kind: "text", text };
  };
  rec.onerror = (e) => {
    if (e.error === "not-allowed" || e.error === "service-not-allowed") heard = { kind: "blocked" };
    else if (e.error !== "no-speech" && e.error !== "aborted") heard = { kind: "failed" };
  };
  rec.onend = () => settle();
  try {
    rec.start();
  } catch {
    return { result: Promise.resolve({ kind: "failed" }), stop: () => {} };
  }
  timers.push(setTimeout(stop, MAX_LISTEN_MS));
  return { result, stop };
}
