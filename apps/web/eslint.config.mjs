import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

// Design-system guard (lib/design/tokens.ts). Tailwind's default palette is switched off in
// app/globals.css, so a raw colour class would silently render nothing: catch it here instead.
const RAW_COLOUR =
  "(?:^|[\\s\"'`:])(?:text|bg|border|from|to|via|ring|divide|fill|stroke|outline|decoration|placeholder|shadow|accent|caret)-" +
  "(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\\d{2,3}\\b" +
  "|(?:text|bg|border|from|to|via|fill|stroke)-\\[#";
const RAW_COLOUR_MESSAGE =
  "Use a design token (bg-surface-raised, text-ink-secondary, bg-brand, text-caution-fg … see lib/design/tokens.ts), not a raw palette colour.";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    files: ["app/**/*.{ts,tsx}", "components/**/*.{ts,tsx}", "lib/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-syntax": [
        "error",
        { selector: `Literal[value=/${RAW_COLOUR}/]`, message: RAW_COLOUR_MESSAGE },
        { selector: `TemplateElement[value.raw=/${RAW_COLOUR}/]`, message: RAW_COLOUR_MESSAGE },
      ],
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
