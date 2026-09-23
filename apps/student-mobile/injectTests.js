const fs = require('fs');
const file = 'src/__tests__/handAiAnalyticsAndFlow.test.ts';
let c = fs.readFileSync(file, 'utf8');

const testSuite = \
  describe('Phase 3.1: Research Benchmark & Ablation Study Layer', () => {
    it('TC1: Verify Baseline A (CRNN_ONLY), Baseline B (CRNN_AI) and System C (CRNN_AI_HUMAN)', () => {
      const trial: any = {
        trialId: 'tc_ablation',
        lines: [
          {
            lineId: 'l1',
            text: 'final human edit', // System C
            ocrText: 'raw ocr wrong',  // Baseline A
            aiSuggestion: 'ai wrong',  // Baseline B
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
      
      // Line 1:
      // A (raw): 'raw ocr wrong' vs 'final human edit' -> wrong (0%)
      // B (ai): 'ai wrong' vs 'final human edit' -> wrong (0%)
      // C (sys): 'final human edit' vs 'final human edit' -> correct (100%)
      
      // Line 2:
      // A: 'perfect match' vs 'perfect match' -> correct (100%)
      // B: 'perfect match' vs 'perfect match' -> correct (100%)
      // C: 'perfect match' vs 'perfect match' -> correct (100%)

      // Overall Accuracies: A: 50%, B: 50%, C: 100%
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
      const analytics = store.currentTrialAnalytics;
      const json = exportTrialToJson(analytics!);
      const parsed = JSON.parse(json);
      expect(parsed.ablationBenchmark).toBeDefined();
      expect(parsed.ablationBenchmark.baselineA).toBeDefined();
      expect(parsed.ablationBenchmark.aiImprovement).toBe(0);
      expect(parsed.ablationBenchmark.humanImprovement).toBe(50);
    });
  });
});
\;

c = c.replace(/    \}\);\n  \}\);\n\}\);/g, '    });\\n  });\\n' + testSuite);
fs.writeFileSync(file, c);
