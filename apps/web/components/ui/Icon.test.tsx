import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import Icon from "./Icon";
import { ICON_NODES } from "./icon-nodes";

describe("Icon", () => {
  it("is decorative unless labelled", () => {
    const html = renderToStaticMarkup(<Icon name="map-pin" />);
    expect(html).toContain('aria-hidden="true"');
    expect(html).not.toContain("role=");
    expect(html).toContain('stroke="currentColor"'); // takes the text colour (tokens)
  });

  it("is an image with a name when it is a control's only content", () => {
    const html = renderToStaticMarkup(<Icon name="x" label="Close" />);
    expect(html).toContain('role="img"');
    expect(html).toContain('aria-label="Close"');
    expect(html).not.toContain("aria-hidden");
  });

  it("draws every node of the Lucide source", () => {
    for (const name of Object.keys(ICON_NODES) as (keyof typeof ICON_NODES)[]) {
      const html = renderToStaticMarkup(<Icon name={name} />);
      expect(html.match(/<(path|circle|line|rect|polyline|polygon)\b/g)?.length, name).toBe(ICON_NODES[name].length);
    }
  });
});
