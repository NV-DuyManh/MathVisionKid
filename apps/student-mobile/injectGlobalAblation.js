const fs = require('fs');
const file = 'src/services/analytics/handAiAnalyticsStore.ts';
let c = fs.readFileSync(file, 'utf8');

const varDecl = \
    let abBaseAAcc = 0, abBaseACer = 0, abBaseAWer = 0, abBaseACharAcc = 0, abBaseAWordAcc = 0;
    let abBaseBAcc = 0, abBaseBCer = 0, abBaseBWer = 0, abBaseBCharAcc = 0, abBaseBWordAcc = 0;
    let abSysCAcc = 0, abSysCCer = 0, abSysCWer = 0, abSysCCharAcc = 0, abSysCWordAcc = 0;
    let abCount = 0;
\;
c = c.replace(
  'let totalLines = 0;',
  varDecl + '\\n    let totalLines = 0;'
);

const loopLogic = \
      if (s.ablationBenchmark) {
        abCount++;
        abBaseAAcc += s.ablationBenchmark.baselineA.accuracy; abBaseACer += s.ablationBenchmark.baselineA.cer; abBaseAWer += s.ablationBenchmark.baselineA.wer; abBaseACharAcc += s.ablationBenchmark.baselineA.characterAccuracy; abBaseAWordAcc += s.ablationBenchmark.baselineA.wordAccuracy;
        abBaseBAcc += s.ablationBenchmark.baselineB.accuracy; abBaseBCer += s.ablationBenchmark.baselineB.cer; abBaseBWer += s.ablationBenchmark.baselineB.wer; abBaseBCharAcc += s.ablationBenchmark.baselineB.characterAccuracy; abBaseBWordAcc += s.ablationBenchmark.baselineB.wordAccuracy;
        abSysCAcc += s.ablationBenchmark.systemC.accuracy; abSysCCer += s.ablationBenchmark.systemC.cer; abSysCWer += s.ablationBenchmark.systemC.wer; abSysCCharAcc += s.ablationBenchmark.systemC.characterAccuracy; abSysCWordAcc += s.ablationBenchmark.systemC.wordAccuracy;
      }
\;
c = c.replace(
  'manual += s.manualEditCount;',
  'manual += s.manualEditCount;\\n' + loopLogic
);

const finalizeLogic = \
    let ablationBenchmark;
    if (abCount > 0) {
      ablationBenchmark = {
        baselineA: { accuracy: +(abBaseAAcc / abCount).toFixed(1), cer: +(abBaseACer / abCount).toFixed(1), wer: +(abBaseAWer / abCount).toFixed(1), characterAccuracy: +(abBaseACharAcc / abCount).toFixed(1), wordAccuracy: +(abBaseAWordAcc / abCount).toFixed(1) },
        baselineB: { accuracy: +(abBaseBAcc / abCount).toFixed(1), cer: +(abBaseBCer / abCount).toFixed(1), wer: +(abBaseBWer / abCount).toFixed(1), characterAccuracy: +(abBaseBCharAcc / abCount).toFixed(1), wordAccuracy: +(abBaseBWordAcc / abCount).toFixed(1) },
        systemC: { accuracy: +(abSysCAcc / abCount).toFixed(1), cer: +(abSysCCer / abCount).toFixed(1), wer: +(abSysCWer / abCount).toFixed(1), characterAccuracy: +(abSysCCharAcc / abCount).toFixed(1), wordAccuracy: +(abSysCWordAcc / abCount).toFixed(1) },
        aiImprovement: +( (abBaseBAcc - abBaseAAcc) / abCount ).toFixed(1),
        humanImprovement: +( (abSysCAcc - abBaseBAcc) / abCount ).toFixed(1),
        errorReductionCer: +( (abBaseACer - abSysCCer) / abCount ).toFixed(1),
        errorReductionWer: +( (abBaseAWer - abSysCWer) / abCount ).toFixed(1),
      };
    }
\;
c = c.replace(
  'const globalCharacterAccuracy = +(Math.max(0, 100 - safeGlobalCer)).toFixed(1);',
  'const globalCharacterAccuracy = +(Math.max(0, 100 - safeGlobalCer)).toFixed(1);\\n' + finalizeLogic
);

c = c.replace(
  /hasCompletedSessions: true,\n\s+totalSessions: validSessions\.length,/,
  \"hasCompletedSessions: true,\\n        ablationBenchmark,\\n        totalSessions: validSessions.length,\"
);

fs.writeFileSync(file, c);
