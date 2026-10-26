import { createElement } from "react";
import { ICON_NODES, type IconName } from "./icon-nodes";

// Inline SVG icons for app chrome (navigation, controls). Emoji stay for content (weather, crops),
// where a colourful glyph helps; chrome needs the same shape on every phone, and emoji vary by
// Android version (🫛 renders as an empty box before Android 13).
//
// Decorative by default (hidden from screen readers — the control's text names it). Pass `label`
// only when the icon is the sole content of a control.
export default function Icon({
  name,
  size = 24,
  label,
  className,
}: {
  name: IconName;
  size?: number;
  label?: string;
  className?: string;
}) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      focusable="false"
      className={className}
      {...(label ? { role: "img", "aria-label": label } : { "aria-hidden": true })}
    >
      {ICON_NODES[name].map(([tag, attrs], i) => createElement(tag, { ...attrs, key: i }))}
    </svg>
  );
}
