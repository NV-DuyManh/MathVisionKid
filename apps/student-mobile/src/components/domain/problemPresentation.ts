/** Presentation only: keep the confirmed OCR source unchanged for editing and APIs. */
export function problemPresentation(source: string): string {
  const labels = [...source.matchAll(/(?:^|\s)([A-Da-d])[.)]\s*(?=\S)/g)];
  // A complete, ordered answer group distinguishes choices from geometry labels
  // or the a/b subquestions of a written exercise.
  if (labels.map(match => match[1].toUpperCase()).join('') !== 'ABCD') return source;
  let start = 0;
  const rows: string[] = [];
  for (const label of labels) {
    rows.push(source.slice(start, label.index).trim());
    start = label.index! + (label[0].length - label[0].trimStart().length);
  }
  rows.push(source.slice(start).trim());
  return rows.filter(Boolean).join('\n');
}
