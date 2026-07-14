import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Bake the weather backend URL into the build. Amplify exposes env vars at
  // build time but not to the SSR runtime, so inlining here (build-time replace)
  // is what makes process.env.WEATHER_API resolve in production. Only set when
  // present so local `next dev` keeps its 127.0.0.1 fallback in page.tsx.
  ...(process.env.WEATHER_API
    ? { env: { WEATHER_API: process.env.WEATHER_API } }
    : {}),
};

export default nextConfig;
