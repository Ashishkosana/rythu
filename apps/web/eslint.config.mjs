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
// Type floor: nothing below 14 px (text-caption). text-xs is 12.75 px at the app's 17 px base.
const BELOW_FLOOR = "(?:^|[\\s\"'`:])text-(?:xs|\\[(?:[0-9]|1[0-3])(?:\\.[0-9]+)?px\\])(?![\\w-])";
const BELOW_FLOOR_MESSAGE = "Text below the 14 px floor: use text-caption (14 px) or larger.";

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
        { selector: `Literal[value=/${BELOW_FLOOR}/]`, message: BELOW_FLOOR_MESSAGE },
        { selector: `TemplateElement[value.raw=/${BELOW_FLOOR}/]`, message: BELOW_FLOOR_MESSAGE },
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
