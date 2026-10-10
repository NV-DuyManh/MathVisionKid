import { ScrollViewStyleReset } from 'expo-router/html';
import type { PropsWithChildren } from 'react';
export default function StudentHtml({ children }: PropsWithChildren) {
  return <html lang="vi"><head>
    <meta charSet="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>MathVisionKid — Cùng em học toán</title>
    <ScrollViewStyleReset />
    <style>{'body{margin:0;background:#F8F7FE}button,a,[role="button"],[role="tab"]{touch-action:manipulation}*:focus-visible{outline:3px solid #7251F8;outline-offset:3px}'}</style>
  </head><body>{children}</body></html>;
}
