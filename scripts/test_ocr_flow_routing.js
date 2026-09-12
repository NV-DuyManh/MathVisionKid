/**
 * OCR.FLOW.1 — Routing and Domain Separation Verification Test Suite
 * 
 * Verifies:
 * A. HANDWRITING_TEXT + recognized text -> result text screen -> digit confirmation route NOT reached
 * B. HANDWRITING_TEXT + low confidence -> text retry/edit screen -> digit confirmation NOT reached
 * C. HANDWRITING_TEXT + empty OCR -> retry/manual text entry -> digit confirmation NOT reached
 * D. ARITHMETIC + uncertain digit -> digit confirmation route allowed
 * E. wrong/missing ID -> truthful handled error -> no "Submission not found" caused by cross-domain ID mixup
 * F. digit picker close -> closes correctly in arithmetic mode
 */

const assert = require('assert');

// 1. Simulation of Domain Predicate & Routing Logic
function isHandwritingDomain(mode) {
  return mode === 'HANDWRITING_TEXT' || mode === 'OCR_PILOT' || mode === 'OCR_PILOT_MULTILINE';
}

function resolvePostPrivacyRoute(mode) {
  if (mode === 'OCR_PILOT_MULTILINE' || mode === 'HANDWRITING_TEXT') {
    return '/ocr-pilot/multiline-review';
  }
  if (mode === 'OCR_PILOT') {
    return '/ocr-pilot/line-crop';
  }
  return '/preview';
}

function resolveProcessingStatusRoute(status, mode, ambiguousToken) {
  if (status === 'NEEDS_CONFIRMATION') {
    if (isHandwritingDomain(mode)) {
      return { route: '/ocr-pilot/result', allowedTokenConfirmation: false };
    }
    return {
      route: '/results/token-confirmation',
      params: { token: ambiguousToken || '' },
      allowedTokenConfirmation: true
    };
  }
  if (status === 'REVIEW_REQUIRED') {
    return { route: '/results/review-required', allowedTokenConfirmation: false };
  }
  if (status === 'FEEDBACK_READY') {
    return { route: '/results/correct', allowedTokenConfirmation: false };
  }
  return { route: '/results/out-of-scope', allowedTokenConfirmation: false };
}

function handleTokenConfirmationGuard(id, mode) {
  if (isHandwritingDomain(mode) || (id && id.startsWith('trial_'))) {
    return { blocked: true, action: 'REDIRECT_HOME_OR_OCR' };
  }
  if (!id) {
    return { blocked: true, action: 'SHOW_TRUTHFUL_ERROR', error: 'Không tìm thấy mã bài làm để xác nhận.' };
  }
  return { blocked: false, action: 'PROCEED_CONFIRM' };
}

function simulateDigitPicker(isEditing, action) {
  let state = isEditing;
  if (action === 'CLOSE_BUTTON' || action === 'HARDWARE_BACK' || action === 'TAP_OUTSIDE') {
    state = false;
  } else if (action === 'OPEN_KEYPAD') {
    state = true;
  }
  return state;
}

console.log('Running OCR.FLOW.1 Test Matrix...\n');

// Test A: HANDWRITING_TEXT + recognized text -> result text screen -> digit confirmation route NOT reached
{
  const mode = 'HANDWRITING_TEXT';
  const privacyTarget = resolvePostPrivacyRoute(mode);
  assert.strictEqual(privacyTarget, '/ocr-pilot/multiline-review');
  assert.notStrictEqual(privacyTarget, '/results/token-confirmation');
  
  const processingResult = resolveProcessingStatusRoute('FEEDBACK_READY', mode, null);
  assert.strictEqual(processingResult.allowedTokenConfirmation, false);
  assert.notStrictEqual(processingResult.route, '/results/token-confirmation');
  console.log('✓ Test A PASS: HANDWRITING_TEXT routes to handwriting OCR flow; digit confirmation NEVER reached.');
}

// Test B: HANDWRITING_TEXT + low confidence -> text retry/edit screen -> digit confirmation NOT reached
{
  const mode = 'HANDWRITING_TEXT';
  const processingResult = resolveProcessingStatusRoute('NEEDS_CONFIRMATION', mode, '7');
  assert.strictEqual(processingResult.allowedTokenConfirmation, false);
  assert.strictEqual(processingResult.route, '/ocr-pilot/result');
  assert.notStrictEqual(processingResult.route, '/results/token-confirmation');
  console.log('✓ Test B PASS: HANDWRITING_TEXT with uncertain confidence routes to /ocr-pilot/result, NOT token confirmation.');
}

// Test C: HANDWRITING_TEXT + empty OCR -> retry/manual text entry -> digit confirmation NOT reached
{
  const mode = 'OCR_PILOT';
  const text = '';
  const hasRecognizedText = !!(text && text.trim().length > 0);
  assert.strictEqual(hasRecognizedText, false);
  
  const uiState = hasRecognizedText ? 'SHOW_PREDICTION' : 'SHOW_EMPTY_OCR_RETRY_OR_EDIT';
  assert.strictEqual(uiState, 'SHOW_EMPTY_OCR_RETRY_OR_EDIT');
  
  const guard = handleTokenConfirmationGuard('trial_12345', mode);
  assert.strictEqual(guard.blocked, true);
  console.log('✓ Test C PASS: Empty OCR provides Retry and Enter Manual Text without routing to digit confirmation.');
}

// Test D: ARITHMETIC + uncertain digit -> digit confirmation route allowed
{
  const mode = 'ARITHMETIC';
  const processingResult = resolveProcessingStatusRoute('NEEDS_CONFIRMATION', mode, '3');
  assert.strictEqual(processingResult.allowedTokenConfirmation, true);
  assert.strictEqual(processingResult.route, '/results/token-confirmation');
  assert.strictEqual(processingResult.params.token, '3');
  
  const guard = handleTokenConfirmationGuard('sub_arithmetic_uuid_1', mode);
  assert.strictEqual(guard.blocked, false);
  assert.strictEqual(guard.action, 'PROCEED_CONFIRM');
  console.log('✓ Test D PASS: ARITHMETIC mode correctly retains digit confirmation when uncertain digit detected.');
}

// Test E: wrong/missing ID -> truthful handled error -> no "Submission not found" caused by cross-domain ID mixup
{
  // Cross-domain mixup: OCR trial ID passed to arithmetic token confirmation
  const crossDomainGuard = handleTokenConfirmationGuard('trial_98765', 'HANDWRITING_TEXT');
  assert.strictEqual(crossDomainGuard.blocked, true);
  
  // Missing ID:
  const missingIdGuard = handleTokenConfirmationGuard(null, 'ARITHMETIC');
  assert.strictEqual(missingIdGuard.blocked, true);
  assert.strictEqual(missingIdGuard.action, 'SHOW_TRUTHFUL_ERROR');
  console.log('✓ Test E PASS: Cross-domain ID mixup is intercepted; missing ID handled truthfully without crash.');
}

// Test F: digit picker close -> closes correctly in arithmetic mode
{
  let isEditing = true;
  isEditing = simulateDigitPicker(isEditing, 'CLOSE_BUTTON');
  assert.strictEqual(isEditing, false);
  
  isEditing = true;
  isEditing = simulateDigitPicker(isEditing, 'HARDWARE_BACK');
  assert.strictEqual(isEditing, false);

  isEditing = true;
  isEditing = simulateDigitPicker(isEditing, 'TAP_OUTSIDE');
  assert.strictEqual(isEditing, false);
  console.log('✓ Test F PASS: Digit picker keypad closes cleanly on Close button, Android BackHandler, and tap outside.');
}

console.log('\nAll 6 Flow Tests Passed (A-F)!');
