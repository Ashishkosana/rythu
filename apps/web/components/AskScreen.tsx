"use client";

// Ask Rythu (S17): type or speak a question; the answer comes only from Rythu's own checked content
// (the server enforces it), with its sources — and the free Kisan Call Centre whenever Rythu can't
// answer, or the farmer still has a doubt. A spoken question gets a spoken answer.

import Link from "next/link";
import { useEffect, useRef, useState, useSyncExternalStore, type FormEvent } from "react";
import LangToggle from "@/components/LangToggle";
import Icon from "@/components/ui/Icon";
import { MAX_QUESTION, askRythu, canAsk, type AskContext, type AskResult } from "@/lib/ask";
import { CROP_LABEL } from "@/lib/cropLabels";
import { KISAN_CALL_CENTRE } from "@/lib/helplines";
import { pick, useLang, type Lang } from "@/lib/lang";
import { listen, recognitionSupported } from "@/lib/listen";
import { PREFS_EVENT, loadCrop, loadPlaceRaw, loadWater, parseSavedPlace } from "@/lib/prefs";
import { speak, stopSpeaking } from "@/lib/speak";

const EXAMPLES: { te: string; en: string }[] = [
  { te: "యూరియా బస్తా ధర ఎంత?", en: "What should a bag of urea cost?" },
  { te: "వరిలో సుడి దోమ వస్తే ఏం చేయాలి?", en: "What to do about brown planthopper in paddy?" },
  { te: "పీఎం కిసాన్ ఎలా పొందాలి?", en: "How do I get PM-Kisan?" },
];

type Status = { kind: "idle" } | { kind: "asking" } | { kind: "listening" } | AskResult;

function subscribePrefs(cb: () => void) {
  window.addEventListener(PREFS_EVENT, cb);
  window.addEventListener("storage", cb);
  return () => {
    window.removeEventListener(PREFS_EVENT, cb);
    window.removeEventListener("storage", cb);
  };
}

const never = () => () => {};

function CallButton({ lang, strong }: { lang: Lang; strong: boolean }) {
  return (
    <a
      href={KISAN_CALL_CENTRE.tel}
      className={`tap mt-3 flex w-full items-center justify-center gap-2 rounded-xl py-2.5 font-semibold ${
        strong ? "bg-brand text-white" : "border border-brand text-brand-ink"
      }`}
    >
      📞 {pick(lang, "కిసాన్ కాల్ సెంటర్", "Kisan Call Centre")} · {KISAN_CALL_CENTRE.display}
    </a>
  );
}

function Result({ status, lang, onListen }: { status: Status; lang: Lang; onListen: (text: string) => void }) {
  if (status.kind === "idle" || status.kind === "listening") return null;
  if (status.kind === "asking") {
    return (
      <p className="card p-4 text-sm text-ink-secondary">
        {pick(lang, "ఆలోచిస్తోంది… 20 సెకన్ల వరకు పట్టవచ్చు.", "Thinking… this can take up to 20 seconds.")}
      </p>
    );
  }
  if (status.kind !== "answer") {
    const text = {
      limit: pick(lang, "ఈరోజు ప్రశ్నలు అయిపోయాయి. రేపు మళ్లీ అడగండి — లేదా ఇప్పుడే ఫోన్ చేయండి.", "Today's questions are used up. Ask again tomorrow — or call now."),
      off: pick(lang, "ప్రశ్నల సేవ ఇప్పుడు అందుబాటులో లేదు. ఉచితంగా ఫోన్ చేసి అడగండి.", "Questions aren't available right now. Call and ask for free."),
      unavailable: pick(lang, "ఇప్పుడు సమాధానం రాలేదు. కాసేపటి తర్వాత మళ్లీ ప్రయత్నించండి.", "No answer right now. Please try again in a little while."),
      offline: pick(lang, "ఇంటర్నెట్ లేదు. ఇంటర్నెట్ ఉన్నప్పుడు అడగండి — లేదా ఫోన్ చేయండి.", "No internet. Ask when you're online — or call."),
    }[status.kind];
    return (
      <section className="card p-4" aria-live="polite">
        <p className="font-medium text-caution-fg">{text}</p>
        <CallButton lang={lang} strong />
      </section>
    );
  }
  const out = status.out;
  const verify = out.sources.some((s) => s.needs_verification);
  return (
    <section className="card p-4" aria-live="polite" aria-labelledby="answer-title">
      <h2 id="answer-title" className="sr-only">{pick(lang, "సమాధానం", "Answer")}</h2>
      <p className="text-lg leading-relaxed">{out.answer}</p>
      <button
        type="button"
        onClick={() => onListen(out.answer)}
        className="tap mt-3 flex items-center gap-2 rounded-xl border border-line-strong px-4 text-sm font-semibold"
      >
        <Icon name="volume-2" size={20} /> {pick(lang, "వినండి", "Listen")}
      </button>
      {out.covered ? (
        <>
          {out.used_todays_weather && (
            <p className="mt-3 text-caption text-ink-secondary">
              {pick(lang, "ఈరోజు మీ ఊరి Rythu వాతావరణ సూచన ఆధారంగా.", "Based on today's Rythu weather read for your village.")}
            </p>
          )}
          {out.sources.length > 0 && (
            <div className="mt-3 border-t border-line pt-3">
              <p className="text-sm font-semibold text-ink-secondary">{pick(lang, "ఆధారం", "Source")}</p>
              <ul className="mt-1 space-y-1">
                {out.sources.map((s) => (
                  <li key={s.id}>
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="tap inline-flex items-center text-sm text-brand-ink underline underline-offset-4"
                    >
                      {s.title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {verify && (
            <p className="mt-3 rounded-xl bg-caution-bg px-3 py-2 text-sm text-caution-fg">
              {pick(lang, "ఇది మీ AEOతో ఒకసారి నిర్ధారించుకోండి.", "Please confirm this with your AEO.")}
            </p>
          )}
          <CallButton lang={lang} strong={false} />
        </>
      ) : (
        <CallButton lang={lang} strong />
      )}
      <p className="mt-3 text-caption text-ink-secondary">
        {pick(lang, `ఈరోజు ఇంకా ${out.remaining_today} ప్రశ్నలు అడగవచ్చు.`, `${out.remaining_today} questions left today.`)}
      </p>
    </section>
  );
}

export default function AskScreen() {
  const { lang } = useLang();
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [micNote, setMicNote] = useState<string | null>(null);
  const stopRef = useRef<(() => void) | null>(null);
  const canListen = useSyncExternalStore(never, recognitionSupported, () => false);
  const place = parseSavedPlace(useSyncExternalStore(subscribePrefs, loadPlaceRaw, () => null));
  const savedCrop = useSyncExternalStore(subscribePrefs, loadCrop, () => null);
  const water = useSyncExternalStore(subscribePrefs, loadWater, () => null);
  const context: AskContext = { lat: place?.lat, lon: place?.lon, crop: savedCrop, water };

  useEffect(() => () => stopSpeaking(), []);

  async function submit(text: string, spoken: boolean) {
    if (!canAsk(text) || status.kind === "asking") return;
    setStatus({ kind: "asking" });
    const result = await askRythu(text, lang, context);
    setStatus(result);
    if (spoken && result.kind === "answer") speak(result.out.answer, lang); // asked by voice → answered by voice
  }

  async function mic() {
    if (status.kind === "listening") {
      stopRef.current?.();
      return;
    }
    setMicNote(null);
    setStatus({ kind: "listening" });
    const { result, stop } = listen(lang);
    stopRef.current = stop;
    const heard = await result;
    stopRef.current = null;
    setStatus({ kind: "idle" });
    if (heard.kind === "text") {
      setQuestion(heard.text);
      void submit(heard.text, true);
    } else {
      setMicNote({
        nothing: pick(lang, "ఏమీ వినిపించలేదు. మళ్లీ మాట్లాడండి.", "Didn't hear anything. Try again."),
        blocked: pick(lang, "మైక్ అనుమతి లేదు — టైప్ చేయండి.", "Microphone not allowed — please type."),
        failed: pick(lang, "వినడం కుదరలేదు — టైప్ చేయండి.", "Couldn't listen — please type."),
      }[heard.kind]);
    }
  }

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    void submit(question, false);
  }

  const crop = savedCrop ? CROP_LABEL[savedCrop] : null;
  const busy = status.kind === "asking";
  return (
    <main className="mx-auto min-h-dvh w-full max-w-md pb-28 text-ink">
      <header className="safe-top rounded-b-[2.25rem] bg-gradient-to-b from-hero-brand-from to-hero-brand-to px-5 pb-6 pt-4 text-white shadow-hero">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">🙋 {pick(lang, "రైతు ప్రశ్న", "Ask Rythu")}</h1>
            <p className="mt-0.5 text-sm text-white/90">
              {pick(lang, "Rythu సరిచూసిన సమాచారం నుంచే సమాధానం", "Answers only from Rythu's checked information")}
            </p>
          </div>
          <LangToggle light />
        </div>
      </header>

      <div className="space-y-3 p-4 pt-6">
        <form onSubmit={onSubmit} className="card space-y-3 p-4">
          <label className="block">
            <span className="text-sm font-medium text-ink-secondary">{pick(lang, "మీ ప్రశ్న", "Your question")}</span>
            <textarea
              value={question}
              maxLength={MAX_QUESTION}
              rows={3}
              onChange={(e) => setQuestion(e.target.value)}
              className="mt-1 w-full resize-none rounded-xl border border-line-strong px-4 py-2.5 text-lg outline-none focus:border-brand"
            />
          </label>
          <div className="flex gap-2">
            {canListen && (
              <button
                type="button"
                onClick={() => void mic()}
                disabled={busy}
                aria-pressed={status.kind === "listening"}
                className={`tap flex flex-1 items-center justify-center gap-2 rounded-xl font-semibold disabled:opacity-60 ${
                  status.kind === "listening" ? "bg-act-fg text-white" : "border border-brand text-brand-ink"
                }`}
              >
                <span aria-hidden>🎤</span>
                {status.kind === "listening" ? pick(lang, "వింటున్నాను… ఆపండి", "Listening… stop") : pick(lang, "మాట్లాడండి", "Speak")}
              </button>
            )}
            <button
              type="submit"
              disabled={busy || !canAsk(question)}
              className="tap flex-1 rounded-xl bg-brand font-semibold text-white disabled:opacity-60"
            >
              {busy ? pick(lang, "అడుగుతోంది…", "Asking…") : pick(lang, "అడగండి", "Ask")}
            </button>
          </div>
          {micNote && <p role="status" className="text-sm text-caution-fg">{micNote}</p>}
          {(place || crop) && (
            <p className="text-caption text-ink-secondary">
              {place && `${pick(lang, "ఊరు", "Village")}: ${place.place}`}
              {place && crop && " · "}
              {crop && `${pick(lang, "పంట", "Crop")}: ${pick(lang, crop.te, crop.en)}`}
            </p>
          )}
        </form>

        <Result status={status} lang={lang} onListen={(t) => speak(t, lang)} />

        {status.kind === "idle" && (
          <section className="card p-4" aria-labelledby="examples">
            <h2 id="examples" className="text-sm font-semibold text-ink-secondary">
              {pick(lang, "ఇలా అడగవచ్చు", "You could ask")}
            </h2>
            <div className="mt-2 flex flex-col gap-2">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.en}
                  type="button"
                  onClick={() => setQuestion(pick(lang, ex.te, ex.en))}
                  className="tap rounded-xl bg-surface-sunken px-4 text-left text-sm"
                >
                  {pick(lang, ex.te, ex.en)}
                </button>
              ))}
            </div>
          </section>
        )}

        <p className="px-2 text-caption leading-relaxed text-ink-secondary">
          {pick(
            lang,
            "మీ ప్రశ్న Rythu సర్వర్‌కు, సమాధానం రాయడానికి Anthropic (Claude)కు వెళ్తుంది — మీ పేరు, ఫోన్ నంబరు, ఆధార్ రాయకండి. రోజుకు 10 ప్రశ్నలు.",
            "Your question goes to Rythu's server and to Anthropic (Claude) to write the answer — don't include your name, phone number or Aadhaar. 10 questions a day.",
          )}
        </p>
        <Link
          href="/privacy/"
          className="tap mx-auto flex w-fit items-center px-4 text-sm font-semibold text-brand-ink underline underline-offset-4"
        >
          {pick(lang, "గోప్యతా విధానం", "Privacy policy")}
        </Link>
      </div>
    </main>
  );
}
