const fs = require('fs');
const file = 'src/__tests__/handAiAnalyticsAndFlow.test.ts';

const testSuite = `

describe('Phase 3.1: Research Benchmark & Ablation Study Layer', () => {
  it('TC1, TC2, TC3, TC4: Verify Baseline A (CRNN_ONLY), Baseline B (CRNN_AI) and System C (CRNN_AI_HUMAN)', () => {
    const trial: any = {
      trialId: 'tc_ablation',
      lines: [
        {
          lineId: 'l1',
          text: 'final human edit',
          ocrText: 'raw ocr wrong',
          aiSuggestion: 'ai wrong',
          groundTruth: 'final human edit',
          groundTruthStatus: 'EXPLICIT',
          verdict: 'CORRECT',
          selectedSource: 'MANUAL',
          confidence: 90
        },
        {
          lineId: 'l2',
          text: 'perfect match',
          ocrText: 'perfect match',
          aiSuggestion: 'perfect match',
          groundTruth: 'perfect match',
          groundTruthStatus: 'EXPLICIT',
          verdict: 'CORRECT',
          selectedSource: 'CRNN_RAW',
          confidence: 95
        }
      ]
    };

    const store = HandAiAnalyticsStore.getInstance();
    const analytics = store.computeTrialAnalytics(trial, true);
    const ab = analytics.ablationBenchmark;
    
    expect(ab).toBeDefined();
    
    expect(ab!.baselineA.accuracy).toBe(50);
    expect(ab!.baselineB.accuracy).toBe(50);
    expect(ab!.systemC.accuracy).toBe(100);

    expect(ab!.aiImprovement).toBe(0);
    expect(ab!.humanImprovement).toBe(50);
    expect(ab!.errorReductionCer).toBeGreaterThanOrEqual(0);
    expect(ab!.errorReductionWer).toBeGreaterThanOrEqual(0);
  });

  it('TC5: Validate that the exported JSON contains the Benchmark & Ablation Study block', () => {
    const store = HandAiAnalyticsStore.getInstance();
    const trial: any = {
      trialId: 'tc_ablation_export',
      lines: [
        {
          lineId: 'l1',
          text: 'final human edit',
          ocrText: 'raw ocr wrong',
          aiSuggestion: 'ai wrong',
          groundTruth: 'final human edit',
          groundTruthStatus: 'EXPLICIT',
          verdict: 'CORRECT',
          selectedSource: 'MANUAL',
          confidence: 90
        }
      ]
    };
    const analytics = store.computeTrialAnalytics(trial, true);
    const json = exportTrialToJson(analytics);
    const parsed = JSON.parse(json);
    expect(parsed.ablationBenchmark).toBeDefined();
    expect(parsed.ablationBenchmark.baselineA).toBeDefined();
    expect(parsed.ablationBenchmark.aiImprovement).toBe(0);
    expect(parsed.ablationBenchmark.humanImprovement).toBe(100);
  });
});
`;

let c = fs.readFileSync(file, 'utf8');
c = c.replace(/    \}\);\n  \}\);\n\}\);/, '    });\n  });\n' + testSuite + '});\n');
fs.writeFileSync(file, c);
