import { ScrollViewStyleReset, useServerDocumentContext } from 'expo-router/html';
import type { PropsWithChildren } from 'react';
import { WEB_DESIGN } from '../constants/theme';

const { colors, focus, motion } = WEB_DESIGN;
const WEB_STYLES = `
  body { margin: 0; background: ${colors.paper}; }
  button, a, [role="button"], [role="tab"] { touch-action: manipulation; }
  *:focus-visible { outline: ${focus.width}px solid ${focus.color}; outline-offset: ${focus.offset}px; }
  ::selection { background: ${colors.star}; color: ${colors.ink}; }
  input, textarea { caret-color: ${colors.blue}; }
  [data-student-paper="true"] {
    background-image: linear-gradient(#1d4ed81c 1px, transparent 1px), linear-gradient(90deg, #1d4ed81c 1px, transparent 1px);
    background-size: 20px 20px;
  }
  [data-student-primary="true"] { transition: transform ${motion.press}ms ease; }
  [data-student-primary="true"]:active:not([aria-disabled="true"]) { transform: translateY(2px); }
  @media (prefers-reduced-motion: reduce) {
    [data-student-primary="true"] { transition: none; }
    [data-student-primary="true"]:active { transform: none; }
  }
`;

export default function StudentHtml({ children }: PropsWithChildren) {
  const { headNodes, bodyNodes, htmlAttributes, bodyAttributes } = useServerDocumentContext();
  return <html {...htmlAttributes} lang="vi"><head>
    <meta charSet="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>MathVisionKid — Cùng em học toán</title>
    <ScrollViewStyleReset />
    <style>{WEB_STYLES}</style>
    {headNodes}
  </head><body {...bodyAttributes}>{children}{bodyNodes}</body></html>;
}
