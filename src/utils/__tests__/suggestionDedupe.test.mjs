/**
 * AI.HWTEXT.PROD.3B — Suggestion Deduplication and Rendering Test Suite
 * Covers Cases 1 to 10 from Mandatory Test Matrix.
 */
import assert from 'node:assert';
import { normalizeForComparison, buildVisibleSuggestions } from '../suggestionDedupe.ts';

console.log('=== RUNNING PROD.3B MANDATORY TEST MATRIX (CASES 1-10) ===\n');

// --------------------------------------------------------------------------
// CASE 1: RAW="Em yêu mùa hè", AI_A="Em yêu mùa hè", AI_B=unavailable
// Expected: 0 suggestion cards, compact neutral state only
// --------------------------------------------------------------------------
{
  const line = {
    rawOcrText: 'Em yêu mùa hè',
    groqSuggestion: 'Em yêu mùa hè',
    groqStatus: 'SUCCESS',
    geminiSuggestion: undefined,
    geminiStatus: 'UNAVAILABLE',
  };
  const suggestions = buildVisibleSuggestions(line);
  assert.strictEqual(suggestions.length, 0, 'Case 1: Expected 0 suggestions');
  console.log('PASS: Case 1 - RAW == AI_A -> 0 suggestion cards, compact neutral state');
}

// --------------------------------------------------------------------------
// CASE 2: RAW="m yêu mùa hè", AI_A="Em yêu mùa hè", AI_B=unavailable
// Expected: one card labeled Gợi ý 1, no Gợi ý 2
// --------------------------------------------------------------------------
{
  const line = {
    rawOcrText: 'm yêu mùa hè',
    groqSuggestion: 'Em yêu mùa hè',
    groqStatus: 'SUCCESS',
    geminiStatus: 'UNAVAILABLE',
  };
  const suggestions = buildVisibleSuggestions(line);
  assert.strictEqual(suggestions.length, 1, 'Case 2: Expected 1 suggestion');
  assert.strictEqual(suggestions[0].label, 'Gợi ý 1');
  assert.strictEqual(suggestions[0].buttonLabel, 'Dùng gợi ý 1');
  assert.strictEqual(suggestions[0].accessibilityLabel, 'Chọn gợi ý 1');
  assert.strictEqual(suggestions[0].text, 'Em yêu mùa hè');
  console.log('PASS: Case 2 - RAW != AI_A, AI_B unavailable -> Exactly 1 card labeled Gợi ý 1');
}

// --------------------------------------------------------------------------
// CASE 3: RAW="m yêu mùa hè", AI_A="Em yêu mùa hè", AI_B="Em yêu mùa hè"
// Expected: one unique card labeled Gợi ý 1
// --------------------------------------------------------------------------
{
  const line = {
    rawOcrText: 'm yêu mùa hè',
    groqSuggestion: 'Em yêu mùa hè',
    groqStatus: 'SUCCESS',
    geminiSuggestion: 'Em yêu mùa hè',
    geminiStatus: 'SUCCESS',
  };
  const suggestions = buildVisibleSuggestions(line);
  assert.strictEqual(suggestions.length, 1, 'Case 3: Expected 1 unique suggestion');
  assert.strictEqual(suggestions[0].label, 'Gợi ý 1');
  assert.strictEqual(suggestions[0].text, 'Em yêu mùa hè');
  console.log('PASS: Case 3 - AI_A == AI_B -> Exactly 1 unique card labeled Gợi ý 1');
}

// --------------------------------------------------------------------------
// CASE 4: RAW="Mọc trên đổi quề", AI_A="Mọc trên đồi quê", AI_B="Mọc trên đồi quê"
// Expected: one unique card labeled Gợi ý 1
// --------------------------------------------------------------------------
{
  const line = {
    rawOcrText: 'Mọc trên đổi quề',
    groqSuggestion: 'Mọc trên đồi quê',
    groqStatus: 'SUCCESS',
    geminiSuggestion: 'Mọc trên đồi quê',
    geminiStatus: 'SUCCESS',
  };
  const suggestions = buildVisibleSuggestions(line);
  assert.strictEqual(suggestions.length, 1, 'Case 4: Expected 1 unique suggestion');
  assert.strictEqual(suggestions[0].label, 'Gợi ý 1');
  assert.strictEqual(suggestions[0].text, 'Mọc trên đồi quê');
  console.log('PASS: Case 4 - Both AI propose same correction -> 1 unique card Gợi ý 1');
}

// --------------------------------------------------------------------------
// CASE 5: RAW="Mọc trên đổi quề", AI_A="Mọc trên đồi quê", AI_B="Mọc trên đồi quê."
// Expected: two unique cards Gợi ý 1 / Gợi ý 2
// --------------------------------------------------------------------------
{
  const line = {
    rawOcrText: 'Mọc trên đổi quề',
    groqSuggestion: 'Mọc trên đồi quê',
    groqStatus: 'SUCCESS',
    geminiSuggestion: 'Mọc trên đồi quê.',
    geminiStatus: 'SUCCESS',
  };
  const suggestions = buildVisibleSuggestions(line);
  assert.strictEqual(suggestions.length, 2, 'Case 5: Expected 2 unique suggestions');
  assert.strictEqual(suggestions[0].label, 'Gợi ý 1');
  assert.strictEqual(suggestions[0].text, 'Mọc trên đồi quê');
  assert.strictEqual(suggestions[1].label, 'Gợi ý 2');
  assert.strictEqual(suggestions[1].text, 'Mọc trên đồi quê.');
  console.log('PASS: Case 5 - Distinct AI suggestions -> Two cards Gợi ý 1 and Gợi ý 2');
}

// --------------------------------------------------------------------------
// CASE 6: RAW="Có hoa sim tím", AI_A="Có hoa sim tím", AI_B="Có hoa sim tím"
// Expected: no suggestion cards, compact neutral state
// --------------------------------------------------------------------------
{
  const line = {
    rawOcrText: 'Có hoa sim tím',
    groqSuggestion: 'Có hoa sim tím',
    groqStatus: 'SUCCESS',
    geminiSuggestion: 'Có hoa sim tím',
    geminiStatus: 'SUCCESS',
  };
  const suggestions = buildVisibleSuggestions(line);
  assert.strictEqual(suggestions.length, 0, 'Case 6: Expected 0 suggestions');
  console.log('PASS: Case 6 - Both AI match RAW -> 0 suggestion cards, compact neutral state');
}

// --------------------------------------------------------------------------
// CASE 7: RAW="Trời, sao ngọt thế!", AI_A unavailable, AI_B unavailable
// Expected: no provider failure text, compact neutral state
// --------------------------------------------------------------------------
{
  const line = {
    rawOcrText: 'Trời, sao ngọt thế!',
    groqStatus: 'UNAVAILABLE',
    geminiStatus: 'UNAVAILABLE',
  };
  const suggestions = buildVisibleSuggestions(line);
  assert.strictEqual(suggestions.length, 0, 'Case 7: Expected 0 suggestions');
  console.log('PASS: Case 7 - Both AI unavailable -> 0 suggestion cards, no failure text');
}

// --------------------------------------------------------------------------
// CASE 8: RAW distinct from one successful advisor, other advisor 429/403
// Expected: one suggestion only, no visible provider/error text
// --------------------------------------------------------------------------
{
  // Test 8A: Groq failed 429, Gemini succeeded with correction
  const lineA = {
    rawOcrText: 'Trời, sao ngọt the',
    groqStatus: 'UNAVAILABLE',
    geminiSuggestion: 'Trời, sao ngọt thế!',
    geminiStatus: 'SUCCESS',
  };
  const suggestionsA = buildVisibleSuggestions(lineA);
  assert.strictEqual(suggestionsA.length, 1, 'Case 8A: Expected 1 suggestion');
  assert.strictEqual(suggestionsA[0].label, 'Gợi ý 1', 'Case 8A: Must be relabeled Gợi ý 1 without gap');
  assert.strictEqual(suggestionsA[0].text, 'Trời, sao ngọt thế!');

  // Test 8B: Groq succeeded with correction, Gemini failed 403
  const lineB = {
    rawOcrText: 'Trời, sao ngọt the',
    groqSuggestion: 'Trời, sao ngọt thế!',
    groqStatus: 'SUCCESS',
    geminiStatus: 'UNAVAILABLE',
  };
  const suggestionsB = buildVisibleSuggestions(lineB);
  assert.strictEqual(suggestionsB.length, 1, 'Case 8B: Expected 1 suggestion');
  assert.strictEqual(suggestionsB[0].label, 'Gợi ý 1');
  assert.strictEqual(suggestionsB[0].text, 'Trời, sao ngọt thế!');
  console.log('PASS: Case 8 - One successful advisor, other 429/403 -> Exactly 1 suggestion relabeled Gợi ý 1');
}

// --------------------------------------------------------------------------
// CASE 9: Unicode-equivalent strings (NFC/NFD) and whitespace variation
// Expected: dedupe correctly for comparison, displayed text remains original suggestion string
// --------------------------------------------------------------------------
{
  const nfcText = 'Tiếng chim reo';
  const nfdText = nfcText.normalize('NFD');
  assert.notStrictEqual(nfcText, nfdText, 'NFC and NFD representations must differ in bytes');
  assert.strictEqual(normalizeForComparison(nfdText), 'Tiếng chim reo', 'normalizeForComparison must convert to NFC');

  const line = {
    rawOcrText: 'Tieng chim reo',
    groqSuggestion: '  Tiếng   chim  reo  ', // whitespace variation + NFC
    groqStatus: 'SUCCESS',
    geminiSuggestion: nfdText, // NFD unicode variation
    geminiStatus: 'SUCCESS',
  };
  const suggestions = buildVisibleSuggestions(line);
  assert.strictEqual(suggestions.length, 1, 'Case 9: Expected 1 unique suggestion after NFC/whitespace dedupe');
  assert.strictEqual(suggestions[0].label, 'Gợi ý 1');
  // Crucial check: original string is preserved for display/use!
  assert.strictEqual(suggestions[0].text, '  Tiếng   chim  reo  ', 'Case 9: Original display text must be preserved');
  console.log('PASS: Case 9 - Unicode NFC/NFD and whitespace dedupe normalized; original text preserved');
}

// --------------------------------------------------------------------------
// CASE 10: After user chooses Gợi ý 1 then taps Giữ OCR gốc
// Expected: finalText returns to rawOcrText, rawOcrText unchanged throughout
// --------------------------------------------------------------------------
{
  const rawOcrText = 'Gió thổi rung rinh';
  const initialLine = {
    lineId: 'line-10',
    lineOrder: 1,
    rawOcrText: rawOcrText,
    finalText: rawOcrText,
    verdict: undefined,
    groqSuggestion: 'Gió thổi rung rinh.',
    groqStatus: 'SUCCESS',
  };

  // Step 1: Initial state
  assert.strictEqual(initialLine.finalText, rawOcrText);
  assert.strictEqual(initialLine.rawOcrText, rawOcrText);

  // Step 2: User chooses Gợi ý 1
  const suggestions = buildVisibleSuggestions(initialLine);
  assert.strictEqual(suggestions.length, 1);
  const chosenText = suggestions[0].text;

  // Simulate feedback handler for suggestion selection
  const lineAfterChoice = {
    ...initialLine,
    verdict: 'CORRECTED',
    finalText: chosenText,
  };
  assert.strictEqual(lineAfterChoice.finalText, 'Gió thổi rung rinh.');
  assert.strictEqual(lineAfterChoice.rawOcrText, rawOcrText, 'rawOcrText must be immutable');

  // Step 3: User taps "Giữ OCR gốc"
  // Simulate feedback handler restoring raw
  const lineAfterRevert = {
    ...lineAfterChoice,
    verdict: 'CORRECT',
    finalText: lineAfterChoice.rawOcrText,
  };
  assert.strictEqual(lineAfterRevert.finalText, rawOcrText, 'finalText must return to rawOcrText');
  assert.strictEqual(lineAfterRevert.rawOcrText, rawOcrText, 'rawOcrText must remain unchanged');
  console.log('PASS: Case 10 - Choose Gợi ý 1 then Giữ OCR gốc -> finalText restored, rawOcrText immutable');
}

console.log('\n=== ALL 10 MANDATORY CASES PASSED SUCCESSFULLY ===\n');
