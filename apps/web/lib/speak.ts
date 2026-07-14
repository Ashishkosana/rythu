// Tap-to-hear for farmers who can't read fast. Uses the phone's built-in
// text-to-speech (Web Speech API) — zero backend, zero cost, works offline once
// the voice is installed. Most Android phones with Google TTS have a Telugu
// (te-IN) voice; if not, we degrade gracefully (Hindi/Indian English, or silence
// rather than a wrong-language robot). A higher-quality Google Cloud TTS te-IN
// path can replace this later without changing callers.

export function speechSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

/** Pick the best available voice for a language: exact locale → base language → null. */
export function pickVoice(
  voices: ReadonlyArray<SpeechSynthesisVoice>,
  lang: "te" | "en",
): SpeechSynthesisVoice | null {
  const want = lang === "te" ? ["te-in", "te"] : ["en-in", "en-gb", "en-us", "en"];
  const norm = (v: SpeechSynthesisVoice) => (v.lang || "").toLowerCase().replace("_", "-");
  for (const w of want) {
    const exact = voices.find((v) => norm(v) === w);
    if (exact) return exact;
  }
  for (const w of want) {
    const base = w.split("-")[0];
    const partial = voices.find((v) => norm(v).startsWith(base));
    if (partial) return partial;
  }
  return null;
}

/** Speak text; returns false if speech isn't possible so the UI can react. */
export function speak(text: string, lang: "te" | "en" = "te"): boolean {
  if (!speechSupported() || !text.trim()) return false;
  const synth = window.speechSynthesis;
  synth.cancel(); // stop any in-progress utterance — one voice at a time
  const u = new SpeechSynthesisUtterance(text);
  const voice = pickVoice(synth.getVoices(), lang);
  if (voice) u.voice = voice;
  u.lang = voice?.lang || (lang === "te" ? "te-IN" : "en-IN");
  u.rate = 0.92; // a touch slower — clearer for older listeners
  synth.speak(u);
  return true;
}

export function stopSpeaking(): void {
  if (speechSupported()) window.speechSynthesis.cancel();
}

/** Build the plain-Telugu spoken summary of today's weather (a farmer's one question). */
export function weatherSpeech(opts: {
  place: string;
  chance: number | null;
  temp: number | null;
  wet: boolean;
}): string {
  const parts: string[] = [];
  const place = opts.place.split("·")[0].trim();
  if (place) parts.push(place);
  if (opts.chance !== null) {
    parts.push(`ఈరోజు వర్షం అవకాశం ${opts.chance} శాతం`);
    parts.push(opts.wet ? "వర్షం రావచ్చు" : "వర్షం అవకాశం తక్కువ");
  } else {
    parts.push("వాతావరణ సమాచారం అందుబాటులో లేదు");
  }
  if (opts.temp !== null) parts.push(`ఉష్ణోగ్రత ${Math.round(opts.temp)} డిగ్రీలు`);
  return parts.join(". ") + ".";
}
