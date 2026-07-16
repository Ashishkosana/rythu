"use client";

import { useEffect, useState } from "react";
import {
  authConfigured,
  confirm,
  currentEmail,
  friendlyError,
  isValidEmail,
  passwordProblem,
  resendCode,
  signIn,
  signOut,
  signUp,
} from "@/lib/auth";

type Mode = "signin" | "signup" | "confirm";

export default function AccountScreen() {
  const configured = authConfigured();
  const [ready, setReady] = useState(!configured); // no async check needed when unconfigured
  const [user, setUser] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!configured) return;
    let alive = true;
    currentEmail()
      .then((e) => {
        if (alive) setUser(e);
      })
      .finally(() => {
        if (alive) setReady(true);
      });
    return () => {
      alive = false;
    };
  }, [configured]);

  async function run(fn: () => Promise<void>, after?: () => void) {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await fn();
      after?.();
    } catch (e) {
      setError(friendlyError(e));
    } finally {
      setBusy(false);
    }
  }

  function doSignup() {
    if (!isValidEmail(email)) return setError("సరైన ఇమెయిల్ ఇవ్వండి · Enter a valid email");
    const pw = passwordProblem(password);
    if (pw) return setError(pw);
    run(
      () => signUp(email, password),
      () => {
        setMode("confirm");
        setNotice("మీ ఇమెయిల్‌కు కోడ్ పంపాం · We emailed you a code");
      },
    );
  }

  function doConfirm() {
    run(
      async () => {
        await confirm(email, code);
        await signIn(email, password); // auto sign-in after verifying
      },
      async () => setUser(await currentEmail()),
    );
  }

  function doSignin() {
    if (!isValidEmail(email)) return setError("సరైన ఇమెయిల్ ఇవ్వండి · Enter a valid email");
    run(
      () => signIn(email, password),
      async () => setUser(await currentEmail()),
    );
  }

  const shell = (children: React.ReactNode) => (
    <div className="mx-auto min-h-dvh max-w-md pb-28 text-stone-900">
      <header className="safe-top rounded-b-[2.25rem] bg-gradient-to-b from-green-700 to-green-800 px-5 pb-6 pt-4 text-white shadow-[var(--shadow-hero)]">
        <h1 className="text-2xl font-bold tracking-tight">👤 ఖాతా</h1>
        <p className="mt-0.5 text-sm text-green-100">ఖాతా అవసరం లేదు — ఫోన్ మార్చినా సమాచారం ఉండేందుకు మాత్రమే</p>
      </header>
      <div className="p-4 pt-6">{children}</div>
    </div>
  );

  if (!configured) {
    return shell(
      <div className="card p-5 text-center">
        <p className="text-3xl">🔧</p>
        <p className="mt-2 font-semibold">లాగిన్ త్వరలో · Login coming soon</p>
        <p className="mt-1 text-sm text-stone-500">అప్పటివరకు యాప్ మొత్తం ఖాతా లేకుండా వాడవచ్చు.</p>
      </div>,
    );
  }
  if (!ready) return shell(<p className="text-center text-stone-500">…</p>);

  if (user) {
    return shell(
      <div className="card p-5 text-center">
        <p className="text-3xl">✅</p>
        <p className="mt-2 text-sm text-stone-500">లాగిన్ అయ్యారు · Signed in</p>
        <p className="mt-1 font-semibold break-all">{user}</p>
        <p className="mt-3 text-xs text-stone-500">మీ ఊరు, పంట సమాచారం ఈ ఖాతాతో సమకాలీకరించబడతాయి.</p>
        <button
          onClick={() => {
            signOut();
            setUser(null);
            setPassword("");
          }}
          className="mt-4 w-full rounded-2xl border border-stone-300 py-3 font-semibold text-stone-700"
        >
          లాగ్ అవుట్ · Sign out
        </button>
      </div>,
    );
  }

  return shell(
    <div className="card p-5">
      <p className="mb-4 rounded-xl bg-green-50 px-3 py-2 text-xs leading-relaxed text-green-900">
        ఖాతా తప్పనిసరి కాదు. మీ ఊరు, పంట వివరాలను వేరే ఫోన్‌లో కూడా పొందేందుకు మాత్రమే. మేము ఏమీ అమ్మము.
      </p>

      {mode !== "confirm" && (
        <div className="mb-4 flex rounded-xl bg-stone-100 p-1">
          {(["signin", "signup"] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => {
                setMode(m);
                setError(null);
                setNotice(null);
              }}
              className={`flex-1 rounded-lg py-2 text-sm font-semibold ${
                mode === m ? "bg-white text-green-800 shadow-[var(--shadow-1)]" : "text-stone-500"
              }`}
            >
              {m === "signin" ? "లాగిన్" : "కొత్త ఖాతా"}
            </button>
          ))}
        </div>
      )}

      {mode === "confirm" ? (
        <div className="space-y-3">
          <p className="text-sm text-stone-600">
            {email} కు వచ్చిన 6-అంకెల కోడ్ నమోదు చేయండి.
          </p>
          <input
            value={code}
            onChange={(e) => setCode(e.target.value)}
            inputMode="numeric"
            placeholder="కోడ్ · Code"
            className="w-full rounded-xl border border-stone-300 px-4 py-3 text-lg tracking-widest outline-none focus:border-green-600"
          />
          <button onClick={doConfirm} disabled={busy} className="w-full rounded-2xl bg-green-700 py-3.5 text-lg font-bold text-white disabled:opacity-60">
            {busy ? "…" : "ధృవీకరించండి · Verify"}
          </button>
          <button
            onClick={() => run(() => resendCode(email), () => setNotice("కోడ్ మళ్లీ పంపాం · Code resent"))}
            className="w-full text-sm font-medium text-green-700"
          >
            కోడ్ మళ్లీ పంపండి · Resend code
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            inputMode="email"
            autoComplete="email"
            placeholder="ఇమెయిల్ · Email"
            className="w-full rounded-xl border border-stone-300 px-4 py-3 outline-none focus:border-green-600"
          />
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            autoComplete={mode === "signup" ? "new-password" : "current-password"}
            placeholder="పాస్‌వర్డ్ · Password"
            className="w-full rounded-xl border border-stone-300 px-4 py-3 outline-none focus:border-green-600"
          />
          {mode === "signup" && (
            <p className="text-xs text-stone-500">కనీసం 8 అక్షరాలు, ఒక అక్షరం + ఒక సంఖ్య.</p>
          )}
          <button
            onClick={mode === "signup" ? doSignup : doSignin}
            disabled={busy}
            className="w-full rounded-2xl bg-green-700 py-3.5 text-lg font-bold text-white disabled:opacity-60"
          >
            {busy ? "…" : mode === "signup" ? "ఖాతా సృష్టించండి · Create account" : "లాగిన్ · Sign in"}
          </button>
        </div>
      )}

      {error && <p className="mt-3 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>}
      {notice && <p className="mt-3 rounded-xl bg-green-50 px-3 py-2 text-sm text-green-800">{notice}</p>}
    </div>,
  );
}
