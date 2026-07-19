"use client";

// Route-level error boundary — a friendly Telugu-first fallback so any unhandled
// render error shows this, never a raw Next 500. A full reload avoids depending on
// the version-specific reset/unstable_retry prop.
export default function Error() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-3 p-8 text-center text-stone-700">
      <p className="text-3xl">🌾</p>
      <p className="font-semibold">ఏదో తప్పు జరిగింది</p>
      <p className="text-sm text-stone-500">Something went wrong · కాసేపటి తర్వాత మళ్లీ చూడండి</p>
      <button
        onClick={() => window.location.reload()}
        className="mt-2 rounded-2xl bg-green-700 px-5 py-2.5 font-semibold text-white"
      >
        మళ్లీ ప్రయత్నించండి · Retry
      </button>
    </main>
  );
}
