import type { MetadataRoute } from "next";

// Rendered once at build time into out/manifest.webmanifest (static export).
export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Rythu — వాతావరణం",
    short_name: "Rythu",
    description: "Honest weather + farming advice for Bhupalpally farmers.",
    id: "/",
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#15803d",
    lang: "te",
    icons: [
      {
        src: "/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      // The photo is full bleed, so any crop an Android launcher mask makes still shows the crop.
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
      // Notification icon: Android paints it as a white mask (Lucide "sprout", ISC licence).
      {
        src: "/icon-monochrome-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "monochrome",
      },
    ],
  };
}
