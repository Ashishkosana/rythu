"use client";

import { useState, useSyncExternalStore } from "react";
import { hasSeenWelcome, markWelcomeSeen } from "@/lib/prefs";
import { speak, stopSpeaking } from "@/lib/speak";

// First-run intro for a farmer new to smartphones: three big icons + one tap to
// HEAR what the app does (reading is the barrier). Shows once, then never again.

const INTRO =
  "నమస్తే. ఇది రైతు యాప్. ఇక్కడ మీ ఊరి వాతావరణం, పంటల సలహా, ప్రభుత్వ పథకాలు తెలుసుకోవచ్చు. మేము ఏమీ అమ్మము.";

const POINTS = [
  { icon: "🌦️", te: "మీ ఊరి వాతావరణం", en: "Your village weather" },
  { icon: "🌱", te: "పంటల సలహా", en: "Crop guidance" },
  { icon: "🏛️", te: "ప్రభుత్వ పథకాలు", en: "Government schemes" },
];

export default function Welcome() {
  // Read localStorage without an effect and without a hydration mismatch: the
  // server snapshot returns `true` (seen → render nothing), then the client
  // re-reads the real value after mount.
  const seen = useSyncExternalStore(
    () => () => {},
    () => hasSeenWelcome(),
    () => true,
  );
  const [dismissed, setDismissed] = useState(false);

  if (seen || dismissed) return null;

  function close() {
    stopSpeaking();
    markWelcomeSeen();
    setDismissed(true);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4 sm:items-center">
      <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-xl">
        <div className="text-center">
          <p className="text-4xl">🌾</p>
          <h1 className="mt-2 text-2xl font-bold">రైతు</h1>
          <p className="mt-1 text-sm text-stone-500">మీ కోసం — మేము ఏమీ అమ్మము</p>
        </div>

        <div className="mt-5 space-y-3">
          {POINTS.map((p) => (
            <div key={p.te} className="flex items-center gap-3 rounded-2xl bg-stone-50 px-4 py-3">
              <span className="text-3xl" aria-hidden>
                {p.icon}
              </span>
              <div>
                <p className="font-semibold">{p.te}</p>
                <p className="text-xs text-stone-400">{p.en}</p>
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={() => speak(INTRO, "te")}
          className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl border-2 border-green-600 py-3 text-base font-semibold text-green-800"
        >
          🔊 వినండి · Listen
        </button>

        <button
          onClick={close}
          className="mt-3 w-full rounded-2xl bg-green-700 py-3.5 text-lg font-bold text-white"
        >
          మొదలుపెట్టండి · Start
        </button>
      </div>
    </div>
  );
}
