import type { NextConfig } from "next";

// A static export: every page is plain HTML/JS/CSS in out/, served by Azure Static Web Apps and
// cached by the service worker (public/sw.js). There is no Node server: data is fetched on the
// device from the API at NEXT_PUBLIC_API_BASE (inlined at build time; lib/api.ts has the dev default).
const nextConfig: NextConfig = {
  output: "export",
  // /crops/ → out/crops/index.html, which every static host serves without rewrite rules.
  trailingSlash: true,
};

export default nextConfig;
