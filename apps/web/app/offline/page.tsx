export const metadata = { title: "ఆఫ్‌లైన్ · Offline — Rythu" };

// A purely static offline fallback (no backend fetch) so the service worker always
// has a safe, honest page to show when the network is down and the requested route
// isn't cached — never a blank screen or a stale error page.
export default function OfflinePage() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-3 p-8 text-center text-stone-700">
      <p className="text-3xl">📴</p>
      <p className="font-semibold">మీరు ఆఫ్‌లైన్‌లో ఉన్నారు</p>
      <p className="text-sm text-stone-500">You&apos;re offline · నెట్‌వర్క్ వచ్చాక మళ్లీ ప్రయత్నించండి</p>
    </main>
  );
}
