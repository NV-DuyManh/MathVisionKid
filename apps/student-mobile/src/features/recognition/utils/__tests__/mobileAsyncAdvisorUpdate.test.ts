import {
  isAdvisorPending,
  mergeTrialWithAdvisorUpdate,
} from '../advisorUpdates';
import { MultilineTrialResult, MultilineLineResult } from '../../api/RecognitionService';

describe('PROD.4B.2R3 Section 7 — Mobile Background Async Update Mechanism', () => {
  const initialTrial: MultilineTrialResult = {
    trialId: 'trial-123',
    status: 'COMPLETED',
    source: 'CAMERA',
    pageImageObjectKey: 'pages/trial-123.jpg',
    pageImageSha256: 'a'.repeat(64),
    pageWidth: 800,
    pageHeight: 600,
    privacyConfirmed: true,
    isTestData: false,
    dataOrigin: 'TEST',
    createdAt: '2026-09-20T12:00:00Z',
    lines: [
      {
        lineId: 'line-1',
        lineOrder: 1,
        predictedText: 'Bó hoa sim tímm',
        rawOcrText: 'Bó hoa sim tímm',
        rawOcrConfidence: 0.88,
        verdict: 'UNVERIFIED',
        trainingEligible: false,
        // Advisors pending on fast-path response:
        groqStatus: undefined,
        geminiStatus: undefined,
        suggestions: [],
      },
      {
        lineId: 'line-2',
        lineOrder: 2,
        predictedText: 'Rừng chiều ngút ngàn',
        rawOcrText: 'Rừng chiều ngút ngàn',
        rawOcrConfidence: 0.95,
        verdict: 'UNVERIFIED',
        trainingEligible: false,
        groqStatus: undefined,
        geminiStatus: undefined,
        suggestions: [],
      },
      {
        lineId: 'line-3',
        lineOrder: 3,
        predictedText: 'Đồi sim tím biếc',
        rawOcrText: 'Đồi sim tím biếc',
        rawOcrConfidence: 0.92,
        verdict: 'UNVERIFIED',
        trainingEligible: false,
        groqStatus: undefined,
        geminiStatus: undefined,
        suggestions: [],
      },
    ],
  };

  test('1 & 2. Initial state reflects fast-path local OCR and detects advisors as PENDING', () => {
    expect(isAdvisorPending(initialTrial)).toBe(true);
    expect(initialTrial.lines[0].rawOcrText).toBe('Bó hoa sim tímm');
  });

  test('backend null advisor statuses remain pending until terminal provider statuses arrive', () => {
    const pending: MultilineTrialResult = JSON.parse(JSON.stringify({
      ...initialTrial,
      lines: [{ ...initialTrial.lines[0], groqStatus: null, geminiStatus: null }],
    }));
    expect(isAdvisorPending(pending)).toBe(true);
    const completed = { ...pending, lines: [{ ...pending.lines[0],
      groqStatus: 'UNAVAILABLE', geminiStatus: 'DISABLED',
    }] };
    expect(isAdvisorPending(completed)).toBe(false);
    expect(mergeTrialWithAdvisorUpdate(pending, completed).lines[0].rawOcrText)
      .toBe(pending.lines[0].rawOcrText);
  });

  test('3, 4 & 5. Delayed advisor completion (e.g. 2500ms): mounted screen receives updates automatically without reload', async () => {
    // Simulate background advisor processing taking 2500ms
    const simulateDelayedAdvisorResponse = async (delayMs: number): Promise<MultilineTrialResult> => {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
      return {
        ...initialTrial,
        correctionSource: 'GROQ_POST_CORRECTION',
        lines: [
          {
            ...initialTrial.lines[0],
            groqSuggestion: 'Bó hoa sim tím',
            groqStatus: 'SUCCESS',
            groqConfidence: 0.96,
            geminiSuggestion: 'Có hoa sim tím',
            geminiStatus: 'SUCCESS',
            geminiConfidence: 0.98,
          },
          {
            ...initialTrial.lines[1],
            groqStatus: 'SUCCESS',
            geminiStatus: 'SUCCESS',
            groqSuggestion: 'Rừng chiều ngút ngàn',
            geminiSuggestion: 'Rừng chiều ngút ngàn',
          },
          {
            ...initialTrial.lines[2],
            groqStatus: 'SUCCESS',
            geminiStatus: 'SUCCESS',
            groqSuggestion: 'Đồi sim tím biếc',
            geminiSuggestion: 'Đồi sim tím biếc',
          },
        ],
      };
    };

    // Test with small synthetic delay representing 2500ms background execution
    const completedTrial = await simulateDelayedAdvisorResponse(50);
    expect(isAdvisorPending(completedTrial)).toBe(false);

    // Merged state without reload
    const merged = mergeTrialWithAdvisorUpdate(initialTrial, completedTrial);
    expect(merged.lines[0].groqSuggestion).toBe('Bó hoa sim tím');
    expect(merged.lines[0].geminiSuggestion).toBe('Có hoa sim tím');
    expect(isAdvisorPending(merged)).toBe(false);
  });

  test('6. Late AI advisor response MUST NOT overwrite user selection or manual edit made before return', () => {
    // Suppose while advisors were in-flight:
    // - Line 1: User explicitly chose OCR ("Giữ OCR gốc", verdict: CORRECT)
    // - Line 2: User manually edited text ("Rừng chiều ngát hương", verdict: CORRECTED, selectedSource: MANUAL_EDIT)
    // - Line 3: Untouched (backend verdict UNVERIFIED)
    const userModifiedTrial: MultilineTrialResult = {
      ...initialTrial,
      lines: [
        {
          ...initialTrial.lines[0],
          verdict: 'CORRECT',
          verifiedTextRaw: 'Bó hoa sim tímm',
          finalText: 'Bó hoa sim tímm',
          predictedText: 'Bó hoa sim tímm',
          selectedSource: 'OCR',
        },
        {
          ...initialTrial.lines[1],
          verdict: 'CORRECTED',
          verifiedTextRaw: 'Rừng chiều ngát hương',
          finalText: 'Rừng chiều ngát hương',
          predictedText: 'Rừng chiều ngát hương',
          currentText: 'Rừng chiều ngát hương',
          selectedSource: 'MANUAL_EDIT',
        },
        {
          ...initialTrial.lines[2],
        },
      ],
    };

    // Background advisors return late with different suggestions and auto-corrections:
    const incomingAdvisorTrial: MultilineTrialResult = {
      ...initialTrial,
      lines: [
        {
          ...initialTrial.lines[0],
          groqSuggestion: 'Bó hoa sim tím',
          geminiSuggestion: 'Có hoa sim tím',
          groqStatus: 'SUCCESS',
          geminiStatus: 'SUCCESS',
          predictedText: 'Bó hoa sim tím', // Advisor wants to suggest/apply this
          finalText: 'Bó hoa sim tím',
        },
        {
          ...initialTrial.lines[1],
          groqSuggestion: 'Rừng chiều bạt ngàn',
          geminiSuggestion: 'Rừng chiều bạt ngàn',
          groqStatus: 'SUCCESS',
          geminiStatus: 'SUCCESS',
          predictedText: 'Rừng chiều bạt ngàn', // Advisor suggestion
          finalText: 'Rừng chiều bạt ngàn',
        },
        {
          ...initialTrial.lines[2],
          groqSuggestion: 'Đồi sim tím ngát',
          geminiSuggestion: 'Đồi sim tím ngát',
          groqStatus: 'SUCCESS',
          geminiStatus: 'SUCCESS',
          predictedText: 'Đồi sim tím ngát',
          finalText: 'Đồi sim tím ngát',
        },
      ],
    };

    const merged = mergeTrialWithAdvisorUpdate(userModifiedTrial, incomingAdvisorTrial);

    // Verify Line 1: User's explicit CORRECT verdict and raw text are preserved!
    expect(merged.lines[0].verdict).toBe('CORRECT');
    expect(merged.lines[0].verifiedTextRaw).toBe('Bó hoa sim tímm');
    expect(merged.lines[0].finalText).toBe('Bó hoa sim tímm');
    // But advisor suggestions are attached for viewing:
    expect(merged.lines[0].groqSuggestion).toBe('Bó hoa sim tím');
    expect(merged.lines[0].geminiSuggestion).toBe('Có hoa sim tím');

    // Verify Line 2: User's manual edit is 100% PRESERVED, late advisor cannot overwrite it!
    expect(merged.lines[1].verdict).toBe('CORRECTED');
    expect(merged.lines[1].verifiedTextRaw).toBe('Rừng chiều ngát hương');
    expect(merged.lines[1].finalText).toBe('Rừng chiều ngát hương');
    expect(merged.lines[1].currentText).toBe('Rừng chiều ngát hương');
    expect(merged.lines[1].selectedSource).toBe('MANUAL_EDIT');
    // Advisor suggestions attached without overriding text:
    expect(merged.lines[1].groqSuggestion).toBe('Rừng chiều bạt ngàn');

    // Verify Line 3: Untouched line received the advisor update!
    expect(merged.lines[2].verdict).toBe('UNVERIFIED');
    expect(merged.lines[2].groqSuggestion).toBe('Đồi sim tím ngát');
    expect(merged.lines[2].finalText).toBe('Đồi sim tím ngát');
  });

  test('a skipped line keeps the student choice when late auto-apply arrives', () => {
    const current = { ...initialTrial, lines: [{ ...initialTrial.lines[0],
      verdict: 'SKIPPED', finalText: initialTrial.lines[0].predictedText,
    }] };
    const incoming = { ...initialTrial, lines: [{ ...initialTrial.lines[0],
      finalText: 'Bó hoa sim tím', predictedText: 'Bó hoa sim tím',
      groqSuggestion: 'Bó hoa sim tím', groqStatus: 'SUCCESS', correctionApplied: true,
    }] };
    const line = mergeTrialWithAdvisorUpdate(current, incoming).lines[0];
    expect(line.verdict).toBe('SKIPPED');
    expect(line.finalText).toBe(current.lines[0].finalText);
    expect(line.predictedText).toBe(current.lines[0].predictedText);
    expect(line.groqSuggestion).toBe('Bó hoa sim tím');
  });

  test('Active editing line guard: do not disturb line being typed in activeEditingLineId', () => {
    const trialDuringEdit: MultilineTrialResult = {
      ...initialTrial,
    };
    const incomingAdvisorTrial: MultilineTrialResult = {
      ...initialTrial,
      lines: [
        {
          ...initialTrial.lines[0],
          groqSuggestion: 'Bó hoa sim tím',
          finalText: 'Bó hoa sim tím',
          predictedText: 'Bó hoa sim tím',
          groqStatus: 'SUCCESS',
        },
      ],
    };

    // Active editing line is line-1
    const merged = mergeTrialWithAdvisorUpdate(trialDuringEdit, incomingAdvisorTrial, 'line-1');
    expect(merged.lines[0].finalText).toBe(trialDuringEdit.lines[0].finalText);
  });
  test('explicit unknown scores clear stale measurements without replacing manual text', () => {
    const current = { ...initialTrial, lines: [{ ...initialTrial.lines[0],
      selectedSource: 'MANUAL_EDIT', finalText: 'Nội dung đã sửa', currentText: 'Nội dung đã sửa',
      groqConfidence: 0.99, groqConfidenceSource: 'AI_SELF_REPORTED',
    }] };
    const incoming = { ...initialTrial, lines: [{ ...initialTrial.lines[0],
      groqConfidence: null, groqConfidenceSource: null, groqStatus: 'UNAVAILABLE',
    }] };
    const line = mergeTrialWithAdvisorUpdate(current, incoming).lines[0];
    expect(line.finalText).toBe('Nội dung đã sửa');
    expect(line.currentText).toBe('Nội dung đã sửa');
    expect(line.groqConfidence).toBeNull();
    expect(line.groqConfidenceSource).toBeNull();
    expect(line.groqStatus).toBe('UNAVAILABLE');
  });

  test.each(['UNVERIFIED', 'CORRECTED'])('late null pending response cannot undo settled advisors for %s', (verdict) => {
    const current = { ...initialTrial, lines: [{ ...initialTrial.lines[0],
      verdict, finalText: 'Bó hoa sim tím', predictedText: 'Bó hoa sim tím',
      groqStatus: 'SUCCESS', geminiStatus: 'SUCCESS',
      groqSuggestion: 'Bó hoa sim tím', geminiSuggestion: 'Bó hoa sim tím',
      groqConfidence: 0.9, groqConfidenceSource: 'AI_SELF_REPORTED',
      correctionApplied: true, correctedText: 'Bó hoa sim tím',
      verifiedTextRaw: verdict === 'CORRECTED' ? 'Nội dung em chọn' : undefined,
    }] };
    const latePending: MultilineTrialResult = JSON.parse(JSON.stringify({
      ...initialTrial, lines: [{ ...initialTrial.lines[0],
        finalText: initialTrial.lines[0].predictedText,
        groqStatus: null, geminiStatus: null, groqSuggestion: null, geminiSuggestion: null,
        groqConfidence: null, geminiConfidence: null, correctionApplied: false,
      }],
    }));
    const merged = mergeTrialWithAdvisorUpdate(current, latePending);
    expect(isAdvisorPending(merged)).toBe(false);
    expect(merged.lines[0]).toMatchObject({
      verdict, finalText: 'Bó hoa sim tím', predictedText: 'Bó hoa sim tím',
      groqStatus: 'SUCCESS', geminiStatus: 'SUCCESS', groqConfidence: 0.9,
      groqSuggestion: 'Bó hoa sim tím', correctionApplied: true,
    });
    expect(merged.lines[0].verifiedTextRaw).toBe(current.lines[0].verifiedTextRaw);
  });

  test('late feedback keeps settled advisors while acknowledging the exact human correction', () => {
    const current = { ...initialTrial, lines: [{ ...initialTrial.lines[0],
      groqStatus: 'SUCCESS', groqSuggestion: 'Bó hoa sim tím',
      finalText: 'Bó hoa sim tím', predictedText: 'Bó hoa sim tím',
    }] };
    const feedback: MultilineTrialResult = JSON.parse(JSON.stringify({
      ...initialTrial, lines: [{ ...initialTrial.lines[0],
        verdict: 'CORRECTED', verifiedTextRaw: 'Bài em tự sửa', finalText: 'Bài em tự sửa',
        predictedText: 'Bài em tự sửa', trainingEligible: true, feedbackAt: '2026-10-03T00:00:00Z',
        groqStatus: null, geminiStatus: null,
      }],
    }));
    const line = mergeTrialWithAdvisorUpdate(current, feedback).lines[0];
    expect(line).toMatchObject({
      verdict: 'CORRECTED', verifiedTextRaw: 'Bài em tự sửa', finalText: 'Bài em tự sửa',
      groqStatus: 'SUCCESS', groqSuggestion: 'Bó hoa sim tím', trainingEligible: true,
      feedbackAt: '2026-10-03T00:00:00Z',
    });
    const otherTrial = { ...feedback, trialId: 'other-trial' };
    expect(mergeTrialWithAdvisorUpdate(current, otherTrial).lines[0].groqStatus).toBeNull();
  });

  test('a terminal failure can still explicitly clear a settled provider score and text', () => {
    const current = { ...initialTrial, lines: [{ ...initialTrial.lines[0],
      groqStatus: 'SUCCESS', groqSuggestion: 'Bó hoa sim tím',
      groqConfidence: 0.9, groqConfidenceSource: 'AI_SELF_REPORTED',
    }] };
    const unavailable: MultilineTrialResult = JSON.parse(JSON.stringify({
      ...initialTrial, lines: [{ ...initialTrial.lines[0],
        groqStatus: 'UNAVAILABLE', groqSuggestion: null,
        groqConfidence: null, groqConfidenceSource: null,
      }],
    }));
    const line = mergeTrialWithAdvisorUpdate(current, unavailable).lines[0];
    expect(line.groqStatus).toBe('UNAVAILABLE');
    expect(line.groqSuggestion).toBeNull();
    expect(line.groqConfidence).toBeNull();
    expect(line.groqConfidenceSource).toBeNull();
  });

});
