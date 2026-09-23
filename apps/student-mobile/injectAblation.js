const fs = require('fs');
const file = 'src/services/analytics/handAiAnalyticsStore.ts';
let content = fs.readFileSync(file, 'utf8');

// 1. Inject variable declarations
const varDecl = \
      let baseBRawCorrect = 0;
      let baseBLevenshteinDist = 0;
      let baseBWordEditDist = 0;
\;
content = content.replace(
  'let finalWordEditDist = 0;',
  'let finalWordEditDist = 0;\n' + varDecl
);

// 2. Inject Baseline B logic in the loop
const baseBLogic = \
      if (isResearchValid) {
        const bPred = (firstSugg || ocrText || '').trim();
        const normBPred = bPred.toLowerCase().replace(/\\s+/g, ' ');
        const normTruth = mandatoryGroundTruth.toLowerCase().replace(/\\s+/g, ' ');
        if (normBPred === normTruth) baseBRawCorrect++;
        baseBLevenshteinDist += computeLevenshteinDistance(bPred, mandatoryGroundTruth);
        baseBWordEditDist += calculateWer(bPred, mandatoryGroundTruth).wordDistance;
      }
\;
content = content.replace(
  'finalWordEditDist += finalWordDist;\n      }',
  'finalWordEditDist += finalWordDist;\n      }\n' + baseBLogic
);

// 3. Inject Ablation calculations
const ablationLogic = \
    // --- Ablation Benchmarking ---
    const baseA_Accuracy = evaluatedLines > 0 ? Math.round((rawCorrect / evaluatedLines) * 100) : 0;
    const baseA_Cer = globalCer;
    const baseA_CharAcc = globalCharacterAccuracy;
    const baseA_Wer = globalWer;
    const baseA_WordAcc = globalWordAccuracy;

    const baseB_Accuracy = evaluatedLines > 0 ? Math.round((baseBRawCorrect / evaluatedLines) * 100) : 0;
    const rawBaseBCer = totalRefCharCount > 0 ? (baseBLevenshteinDist / totalRefCharCount) * 100 : 0;
    const baseB_Cer = +(Math.min(100, isNaN(rawBaseBCer) || !isFinite(rawBaseBCer) ? 0 : rawBaseBCer)).toFixed(1);
    const baseB_CharAcc = +(Math.max(0, 100 - baseB_Cer)).toFixed(1);
    const rawBaseBWer = totalRefWordCount > 0 ? (baseBWordEditDist / totalRefWordCount) * 100 : 0;
    const baseB_Wer = +(Math.min(100, isNaN(rawBaseBWer) || !isFinite(rawBaseBWer) ? 0 : rawBaseBWer)).toFixed(1);
    const baseB_WordAcc = +(Math.max(0, 100 - baseB_Wer)).toFixed(1);

    const sysC_Accuracy = finalAccuracy;
    const rawSysCCer = totalRefCharCount > 0 ? (finalLevenshteinDist / totalRefCharCount) * 100 : 0;
    const sysC_Cer = +(Math.min(100, isNaN(rawSysCCer) || !isFinite(rawSysCCer) ? 0 : rawSysCCer)).toFixed(1);
    const sysC_CharAcc = +(Math.max(0, 100 - sysC_Cer)).toFixed(1);
    const rawSysCWer = totalRefWordCount > 0 ? (finalWordEditDist / totalRefWordCount) * 100 : 0;
    const sysC_Wer = +(Math.min(100, isNaN(rawSysCWer) || !isFinite(rawSysCWer) ? 0 : rawSysCWer)).toFixed(1);
    const sysC_WordAcc = +(Math.max(0, 100 - sysC_Wer)).toFixed(1);

    const ablationBenchmark: AblationBenchmarkResult = {
      baselineA: { accuracy: baseA_Accuracy, characterAccuracy: baseA_CharAcc, wordAccuracy: baseA_WordAcc, cer: baseA_Cer, wer: baseA_Wer },
      baselineB: { accuracy: baseB_Accuracy, characterAccuracy: baseB_CharAcc, wordAccuracy: baseB_WordAcc, cer: baseB_Cer, wer: baseB_Wer },
      systemC: { accuracy: sysC_Accuracy, characterAccuracy: sysC_CharAcc, wordAccuracy: sysC_WordAcc, cer: sysC_Cer, wer: sysC_Wer },
      aiImprovement: Math.max(0, baseB_Accuracy - baseA_Accuracy),
      humanImprovement: Math.max(0, sysC_Accuracy - baseB_Accuracy),
      errorReductionCer: Math.max(0, +(baseA_Cer - sysC_Cer).toFixed(1)),
      errorReductionWer: Math.max(0, +(baseA_Wer - sysC_Wer).toFixed(1))
    };
\;
content = content.replace(
  '// Error Analysis Report',
  ablationLogic + '\n    // Error Analysis Report'
);

// 4. Inject into TrialAnalytics return object
content = content.replace(
  'metricProvenance: {',
  'ablationBenchmark,\n        metricProvenance: {'
);

fs.writeFileSync(file, content);
