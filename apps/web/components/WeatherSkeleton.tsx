// First paint before any forecast exists on this device (first install, or a new village):
// the screen's shape, no numbers. Server-renderable, so the static shell shows it instantly.

export default function WeatherSkeleton() {
  return (
    <div className="mx-auto min-h-dvh w-full max-w-md pb-28" aria-busy="true" aria-label="వాతావరణం లోడ్ అవుతోంది · Loading weather">
      <div className="safe-top rounded-b-[2.25rem] bg-gradient-to-b from-hero-clear-from to-hero-clear-to px-4 pb-6 pt-3 text-white">
        <span className="text-base font-bold tracking-tight">🌾 రైతు</span>
        <div className="mt-3 h-12 animate-pulse rounded-2xl bg-white/30 motion-reduce:animate-none" />
        <div className="mt-5 flex items-end justify-between">
          <div className="space-y-2">
            <div className="h-4 w-40 rounded bg-white/30" />
            <div className="h-20 w-32 animate-pulse rounded-2xl bg-white/30 motion-reduce:animate-none" />
          </div>
          <div className="h-24 w-20 animate-pulse rounded-2xl bg-white/30 motion-reduce:animate-none" />
        </div>
        <div className="mt-4 h-12 rounded-2xl bg-white/20" />
      </div>
      <div className="space-y-4 px-4 pt-6">
        <div className="card h-36 animate-pulse motion-reduce:animate-none" />
        <div className="card h-24 animate-pulse motion-reduce:animate-none" />
      </div>
    </div>
  );
}
