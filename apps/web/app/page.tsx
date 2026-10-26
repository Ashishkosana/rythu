import { Suspense } from "react";
import HomeScreen from "@/components/HomeScreen";
import WeatherSkeleton from "@/components/WeatherSkeleton";

// A static shell: the skeleton is in the HTML, so it paints before any script runs. The forecast
// is fetched on the device (components/HomeScreen.tsx → lib/useWeather.ts), from its saved copy first.
export default function Page() {
  return (
    <Suspense fallback={<WeatherSkeleton />}>
      <HomeScreen />
    </Suspense>
  );
}
