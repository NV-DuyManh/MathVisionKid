import type { MultilineLineResult } from '../services/api/OcrPilotService';

export interface AdvisorView {
  provider: 'GROQ' | 'GEMINI';
  model: string;
  status: 'SUCCESS' | 'NOT_TRIGGERED' | 'UNAVAILABLE' | 'DISABLED' | 'ERROR';
  text: string;
  confidence: number;
  decision?: string;
  wasTriggered: boolean;
}

export interface VisibleSuggestion {
  id: string; // 'sugg-1' | 'sugg-2'
  label: string; // 'Gợi ý 1' | 'Gợi ý 2'
  buttonLabel: string; // 'Dùng gợi ý 1' | 'Dùng gợi ý 2'
  accessibilityLabel: string; // 'Chọn gợi ý 1' | 'Chọn gợi ý 2'
  text: string; // Original, unnormalized string for display and application
  confidence?: number;
  decision?: string;
  provider?: 'GROQ' | 'GEMINI'; // Preserved internally for diagnostics/audit; NEVER shown in student UI
}

/**
 * Builds the internal advisor view for a given provider.
 */
export function buildAdvisorView(
  line: Partial<MultilineLineResult>,
  provider: 'GROQ' | 'GEMINI'
): AdvisorView {
  const fromSuggestions = Array.isArray(line.suggestions)
    ? line.suggestions.find((s) => s.provider === provider)
    : undefined;

  let directText = provider === 'GROQ' ? line.groqSuggestion : line.geminiSuggestion;
  const directStatus = provider === 'GROQ' ? line.groqStatus : line.geminiStatus;
  const directModel = provider === 'GROQ' ? line.groqModel : line.geminiModel;
  const directConfidence = provider === 'GROQ' ? line.groqConfidence : line.geminiConfidence;
  const directDecision = provider === 'GROQ' ? line.groqDecision : line.geminiDecision;

  // Fallback for Groq legacy correctedText
  if (provider === 'GROQ' && !directText && line.correctedText && directStatus !== 'UNAVAILABLE') {
    directText = line.correctedText;
  }

  const text = (directText || fromSuggestions?.text || '').trim();
  const rawModel = directModel || fromSuggestions?.model;
  const model = rawModel || provider;
  const confidence = directConfidence ?? fromSuggestions?.confidence ?? 0.0;
  const decision = directDecision || fromSuggestions?.decision || 'KEEP_RAW';

  const wasTriggered = Boolean(
    line.correctionApplied ||
    (line.correctedText && line.correctedText !== line.rawOcrText) ||
    line.groqStatus ||
    line.geminiStatus ||
    line.groqSuggestion ||
    line.geminiSuggestion ||
    (Array.isArray(line.suggestions) && line.suggestions.some((s) => s.provider === provider))
  );

  const rawStatus = (directStatus || fromSuggestions?.status || '').toUpperCase();
  let status: 'SUCCESS' | 'NOT_TRIGGERED' | 'UNAVAILABLE' | 'DISABLED' | 'ERROR';

  if (text.length > 0) {
    status = 'SUCCESS';
  } else if (rawStatus === 'UNAVAILABLE') {
    status = 'UNAVAILABLE';
  } else if (rawStatus === 'DISABLED') {
    status = 'DISABLED';
  } else if (rawStatus === 'ERROR') {
    status = 'ERROR';
  } else if (wasTriggered) {
    status = 'UNAVAILABLE';
  } else {
    status = 'NOT_TRIGGERED';
  }

  return {
    provider,
    model,
    status,
    text,
    confidence,
    decision,
    wasTriggered,
  };
}

/**
 * Normalizes strings strictly for equality comparison.
 * - Trims outer whitespace
 * - Normalizes Unicode consistently (NFC)
 * - Collapses accidental repeated internal whitespace into a single space
 * - Does NOT change displayed/original suggestion text
 * - Does NOT alter spelling semantically
 */
export function normalizeForComparison(str: string | null | undefined): string {
  if (!str) return '';
  return str
    .trim()
    .normalize('NFC')
    .replace(/\s+/g, ' ');
}

/**
 * Builds visible, deduplicated suggestions for a line in the student UI.
 *
 * Rules:
 * 1. Filter out suggestions that match the RAW OCR text (not distinct).
 * 2. Dedupe identical suggestions against each other (keeps first unique).
 * 3. Max 2 unique suggestions returned.
 * 4. Deterministic sequential numbering:
 *    - First unique suggestion -> "Gợi ý 1", button "Dùng gợi ý 1"
 *    - Second unique suggestion -> "Gợi ý 2", button "Dùng gợi ý 2"
 * 5. Provider identities (Groq, Gemini) are NEVER exposed in labels or student UI.
 * 6. If no unique suggestions remain, returns [] (UI renders compact neutral state).
 */
export function buildVisibleSuggestions(
  line: Partial<MultilineLineResult>
): VisibleSuggestion[] {
  const rawOcr = line.rawOcrText || line.predictedText || '';
  const normRaw = normalizeForComparison(rawOcr);

  // Collect candidate views in stable order: Groq (Advisor A) then Gemini (Advisor B)
  const groqView = buildAdvisorView(line, 'GROQ');
  const geminiView = buildAdvisorView(line, 'GEMINI');

  const candidates: {
    text: string;
    confidence?: number;
    decision?: string;
    provider: 'GROQ' | 'GEMINI';
  }[] = [];

  const rawGroqText = line.groqSuggestion ?? (line.correctedText && line.groqStatus !== 'UNAVAILABLE' ? line.correctedText : undefined) ?? line.suggestions?.find((s) => s.provider === 'GROQ')?.text ?? '';
  const rawGeminiText = line.geminiSuggestion ?? line.suggestions?.find((s) => s.provider === 'GEMINI')?.text ?? '';

  if (groqView.status === 'SUCCESS' && rawGroqText && rawGroqText.trim().length > 0) {
    candidates.push({
      text: rawGroqText,
      confidence: groqView.confidence,
      decision: groqView.decision,
      provider: 'GROQ',
    });
  }

  if (geminiView.status === 'SUCCESS' && rawGeminiText && rawGeminiText.trim().length > 0) {
    candidates.push({
      text: rawGeminiText,
      confidence: geminiView.confidence,
      decision: geminiView.decision,
      provider: 'GEMINI',
    });
  }

  const visible: VisibleSuggestion[] = [];
  const seenNorms: string[] = [];

  for (const cand of candidates) {
    const normCand = normalizeForComparison(cand.text);

    // Rule A & B: If suggestion equals RAW OCR text, it is not distinct -> hide it
    if (normCand === normRaw) {
      continue;
    }

    // Rule C: If duplicate of an earlier surviving suggestion -> hide it
    if (seenNorms.includes(normCand)) {
      continue;
    }

    // Max 2 unique suggestions
    if (visible.length >= 2) {
      break;
    }

    seenNorms.push(normCand);
    const index = visible.length + 1; // 1 or 2
    visible.push({
      id: `sugg-${index}`,
      label: `Gợi ý ${index}`,
      buttonLabel: `Dùng gợi ý ${index}`,
      accessibilityLabel: `Chọn gợi ý ${index}`,
      text: cand.text, // keep original display text untouched
      confidence: cand.confidence,
      decision: cand.decision,
      provider: cand.provider,
    });
  }

  return visible;
}
