// The brand header every secondary screen opens with: the screen's title (its one h1), an optional
// line under it, and the language toggle. (The home screen has its own weather hero instead.)

import LangToggle from "@/components/LangToggle";

const TITLE = "text-2xl font-bold tracking-tight";

export default function ScreenHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <header className="safe-top rounded-b-[2.25rem] bg-gradient-to-b from-hero-brand-from to-hero-brand-to px-5 pb-6 pt-4 text-white shadow-hero">
      <div className="flex items-start justify-between gap-2">
        {subtitle ? (
          <div>
            <h1 className={TITLE}>{title}</h1>
            <p className="mt-0.5 text-sm text-white/90">{subtitle}</p>
          </div>
        ) : (
          <h1 className={TITLE}>{title}</h1>
        )}
        <LangToggle light />
      </div>
    </header>
  );
}
