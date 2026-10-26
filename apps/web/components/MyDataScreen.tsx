"use client";

// "My data": what Rythu knows about the farmer, where it is kept, and the controls over it (DPDP Act:
// consent before anything leaves the phone; delete on request). Short sentences, both languages —
// the screen has to make sense to someone new to smartphones.

import { useQueryClient } from "@tanstack/react-query";
import { createStore, del } from "idb-keyval";
import { useState, useSyncExternalStore } from "react";
import LangToggle from "@/components/LangToggle";
import Icon from "@/components/ui/Icon";
import { CROP_LABEL } from "@/lib/cropLabels";
import { pick, useLang } from "@/lib/lang";
import {
  PREFS_EVENT,
  clearAllPrefs,
  loadCrop,
  loadPlaceRaw,
  parseSavedPlace,
  syncConsent,
} from "@/lib/prefs";
import { deleteServerData, setConsent, subscribeSyncStatus, syncStatus, type SyncStatus } from "@/lib/profileSync";

function subscribePrefs(cb: () => void) {
  window.addEventListener(PREFS_EVENT, cb);
  window.addEventListener("storage", cb);
  return () => {
    window.removeEventListener(PREFS_EVENT, cb);
    window.removeEventListener("storage", cb);
  };
}

const OFF: SyncStatus = { state: "off" };

export default function MyDataScreen() {
  const { lang } = useLang();
  const queryClient = useQueryClient();
  const consent = useSyncExternalStore(subscribePrefs, syncConsent, () => false);
  const status = useSyncExternalStore(subscribeSyncStatus, syncStatus, () => OFF);
  const place = parseSavedPlace(useSyncExternalStore(subscribePrefs, loadPlaceRaw, () => null));
  const crop = useSyncExternalStore(subscribePrefs, loadCrop, () => null);
  const [confirm, setConfirm] = useState<null | "server" | "phone">(null);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);

  async function deleteServer() {
    setBusy(true);
    const ok = await deleteServerData();
    setBusy(false);
    setConfirm(null);
    setNote(
      ok
        ? { ok: true, text: pick(lang, "సర్వర్ నుండి తొలగించాం.", "Deleted from Rythu's server.") }
        : { ok: false, text: pick(lang, "ఇప్పుడు కుదరలేదు — ఇంటర్నెట్ ఉన్నప్పుడు మళ్లీ ప్రయత్నించండి.", "Couldn't reach Rythu — try again with internet.") },
    );
  }

  async function clearPhone() {
    setBusy(true);
    const ok = await deleteServerData(); // the server copy first: after this the phone forgets how to reach it
    if (!ok) {
      setBusy(false);
      setConfirm(null);
      setNote({ ok: false, text: pick(lang, "ముందు సర్వర్ నుండి తొలగించాలి — ఇంటర్నెట్ ఉన్నప్పుడు మళ్లీ ప్రయత్నించండి.", "The server copy must go first — try again with internet.") });
      return;
    }
    queryClient.clear();
    await del("rythu.queries", createStore("rythu", "query-cache")).catch(() => undefined);
    clearAllPrefs();
    // A full reload on purpose (not router.push): nothing of the old state may survive in memory.
    window.location.replace(`${window.location.origin}/`);
  }

  return (
    <main className="mx-auto min-h-dvh w-full max-w-md pb-28 text-ink">
      <header className="safe-top rounded-b-[2.25rem] bg-gradient-to-b from-hero-brand-from to-hero-brand-to px-5 pb-6 pt-4 text-white shadow-hero">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{pick(lang, "నా సమాచారం", "My data")}</h1>
            <p className="mt-0.5 text-sm text-white/90">{pick(lang, "మీ సమాచారం మీదే", "Your data is yours")}</p>
          </div>
          <LangToggle light />
        </div>
      </header>

      <div className="space-y-4 p-4 pt-6">
        <section className="card p-4" aria-labelledby="on-phone">
          <h2 id="on-phone" className="flex items-center gap-2 text-lg font-bold">
            <Icon name="map-pin" size={20} className="text-brand-ink" /> {pick(lang, "ఈ ఫోన్‌లో", "On this phone")}
          </h2>
          <dl className="mt-3 space-y-2 text-sm">
            <Row label={pick(lang, "ఊరు", "Village")} value={place?.place ?? pick(lang, "ఎంచుకోలేదు", "Not chosen")} />
            <Row label={pick(lang, "పంట", "Crop")} value={crop ? `${CROP_LABEL[crop].emoji} ${CROP_LABEL[crop][lang]}` : pick(lang, "ఎంచుకోలేదు", "Not chosen")} />
            <Row label={pick(lang, "భాష", "Language")} value={lang === "te" ? "తెలుగు" : "English"} />
          </dl>
        </section>

        <section className="card p-4" aria-labelledby="server-copy">
          <div className="flex items-start justify-between gap-3">
            <h2 id="server-copy" className="text-lg font-bold">
              {pick(lang, "Rythu సర్వర్‌లో కాపీ", "Copy on Rythu's server")}
            </h2>
            <button
              role="switch"
              aria-checked={consent}
              aria-labelledby="server-copy"
              disabled={busy}
              onClick={() => {
                setNote(null);
                void setConsent(!consent);
              }}
              className={`tap relative flex shrink-0 items-center rounded-full px-1 transition-colors ${consent ? "bg-brand" : "bg-line-strong"}`}
            >
              <span className={`h-9 w-9 rounded-full bg-white shadow-1 transition-transform ${consent ? "translate-x-6" : ""}`} />
              <span className="w-6" aria-hidden />
            </button>
          </div>
          <p className="mt-2 text-sm text-ink-secondary">
            {pick(
              lang,
              "వర్ష హెచ్చరికలు మీకు పంపాలంటే మీ ఊరు, పంట, భాష మాత్రమే మా సర్వర్‌లో ఉంచుతాం. పేరు, ఫోన్ నంబర్ అడగము.",
              "To send you rain alerts, we keep only your village, crop and language on our server. We never ask for your name or phone number.",
            )}
          </p>
          <StatusLine status={consent ? status : OFF} lang={lang} />
        </section>

        <section className="card space-y-3 p-4" aria-labelledby="delete">
          <h2 id="delete" className="text-lg font-bold">
            {pick(lang, "తొలగించండి", "Delete")}
          </h2>
          {confirm === null ? (
            <>
              <button
                onClick={() => setConfirm("server")}
                className="tap w-full rounded-2xl border border-line-strong px-4 py-3 font-semibold text-act-fg"
              >
                {pick(lang, "సర్వర్ నుండి నా సమాచారం తొలగించండి", "Delete my data from Rythu's server")}
              </button>
              <button
                onClick={() => setConfirm("phone")}
                className="tap w-full rounded-2xl border border-line-strong px-4 py-3 font-semibold text-act-fg"
              >
                {pick(lang, "ఈ ఫోన్ నుండి కూడా అంతా తొలగించండి", "Also clear everything on this phone")}
              </button>
            </>
          ) : (
            <div role="alertdialog" aria-labelledby="confirm-text" className="rounded-2xl bg-act-bg p-4">
              <p id="confirm-text" className="font-semibold text-act-fg">
                {confirm === "server"
                  ? pick(lang, "సర్వర్‌లో ఉన్న మీ సమాచారం శాశ్వతంగా తొలగిపోతుంది. సరేనా?", "Your data on Rythu's server will be deleted for good. OK?")
                  : pick(lang, "సర్వర్‌తో పాటు ఈ ఫోన్‌లోని ఊరు, పంట, సేవ్ చేసిన వాతావరణం అన్నీ తొలగిపోతాయి. సరేనా?", "This deletes the server copy AND this phone's village, crop and saved forecast. OK?")}
              </p>
              <div className="mt-3 flex gap-2">
                <button
                  disabled={busy}
                  onClick={() => void (confirm === "server" ? deleteServer() : clearPhone())}
                  className="tap flex-1 rounded-xl bg-act-fg px-4 py-2.5 font-semibold text-white disabled:opacity-60"
                >
                  {busy ? "…" : pick(lang, "అవును, తొలగించు", "Yes, delete")}
                </button>
                <button
                  disabled={busy}
                  onClick={() => setConfirm(null)}
                  className="tap flex-1 rounded-xl border border-line-strong bg-surface-raised px-4 py-2.5 font-semibold"
                >
                  {pick(lang, "వద్దు", "Cancel")}
                </button>
              </div>
            </div>
          )}
          {note && (
            <p role="status" className={`rounded-xl px-3 py-2 text-sm ${note.ok ? "bg-success-bg text-success-fg" : "bg-caution-bg text-caution-fg"}`}>
              {note.text}
            </p>
          )}
        </section>

        <p className="px-2 text-center text-sm text-ink-secondary">
          {pick(lang, "Rythu ఏమీ అమ్మదు. మీ సమాచారం ఎవరికీ ఇవ్వదు.", "Rythu sells nothing and shares your data with no one.")}
        </p>
      </div>
    </main>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-ink-secondary">{label}</dt>
      <dd className="text-right font-medium">{value}</dd>
    </div>
  );
}

function StatusLine({ status, lang }: { status: SyncStatus; lang: "te" | "en" }) {
  const [icon, text, tone] = (() => {
    switch (status.state) {
      case "off":
        return ["x", pick(lang, "ఆఫ్ — ఏదీ ఈ ఫోన్ దాటి వెళ్లదు", "Off — nothing leaves this phone"), "text-ink-secondary"] as const;
      case "syncing":
        return ["check", pick(lang, "సేవ్ అవుతోంది…", "Saving…"), "text-ink-secondary"] as const;
      case "saved":
        return ["check", pick(lang, "సర్వర్‌లో సేవ్ అయింది", "Saved on Rythu's server"), "text-success-fg"] as const;
      case "failed":
        return ["wifi-off", pick(lang, "ఇప్పుడు సేవ్ కాలేదు — మళ్లీ ప్రయత్నిస్తాం", "Couldn't save now — will try again"), "text-caution-fg"] as const;
    }
  })();
  return (
    <p role="status" className={`mt-3 flex items-center gap-1.5 text-sm font-medium ${tone}`}>
      <Icon name={icon} size={18} /> {text}
    </p>
  );
}
