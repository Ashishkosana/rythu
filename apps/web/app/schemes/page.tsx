import { SCHEMES } from "@/lib/schemes";

export const metadata = { title: "పథకాలు · Schemes — Rythu" };

export default function SchemesPage() {
  return (
    <div className="mx-auto min-h-dvh max-w-md pb-28 text-stone-900">
      <header className="safe-top sticky top-0 z-20 bg-green-800 px-4 py-3 text-white shadow-sm">
        <span className="text-lg font-bold">🏛️ ప్రభుత్వ పథకాలు</span>
        <p className="text-xs text-green-100">రైతులకు ఉపయోగపడే పథకాలు · Benefits for farmers</p>
      </header>

      <div className="space-y-3 p-4">
        {SCHEMES.map((s) => (
          <div key={s.key} className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
            <h2 className="text-lg font-semibold">
              {s.name_te} <span className="text-sm font-normal text-stone-500">· {s.name_en}</span>
            </h2>

            <p className="mt-2 text-sm">
              {s.what_te}
              <span className="block text-xs text-stone-400">{s.what_en}</span>
            </p>

            <div className="mt-3 space-y-2 text-sm">
              <p>
                <span className="font-medium text-green-800">ఎవరికి · Who: </span>
                {s.who_te}
                <span className="block text-xs text-stone-400">{s.who_en}</span>
              </p>
              <p>
                <span className="font-medium text-green-800">ఎలా · How: </span>
                {s.how_te}
                <span className="block text-xs text-stone-400">{s.how_en}</span>
              </p>
            </div>

            <a
              href={s.url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-block rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white"
            >
              అధికారిక వెబ్‌సైట్ · Official site →
            </a>
          </div>
        ))}

        <p className="px-1 text-xs text-stone-400">
          మొత్తాలు, అర్హతలు ఏటా మారవచ్చు — అధికారిక వెబ్‌సైట్ లేదా మీ AEOని సంప్రదించండి. Rythu ఏమీ అమ్మదు.
        </p>
      </div>
    </div>
  );
}
