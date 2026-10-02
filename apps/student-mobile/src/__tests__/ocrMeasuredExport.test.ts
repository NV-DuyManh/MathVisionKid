import { RecognitionAnalyticsStore, exportTrialToJson } from '../features/recognition/analytics/recognitionAnalyticsStore';
import type { MultilineTrialResult } from '../features/recognition/api/RecognitionService';

test('export requires an independent reference and keeps manual gains separate from provider output', () => {
  const store = new RecognitionAnalyticsStore();
  const trial = { trialId: 'actual-1', lines: [{
    lineId: 'line-1', rawOcrText: 'xin chao', predictedText: 'xin chao',
    currentText: 'xin chào', finalText: 'xin chào', verdict: 'CORRECTED', selectedSource: 'MANUAL_EDIT',
    rawOcrConfidence: 0, rawOcrConfidenceSource: 'CRNN_CTC_SOFTMAX',
    groqSuggestion: 'xin chao', groqStatus: 'SUCCESS', groqModel: 'real-provider-model',
  }] } as MultilineTrialResult;
  const unlabeled = JSON.parse(exportTrialToJson(store.computeTrialAnalytics(trial, true)));
  expect(unlabeled.measuredMetrics.rawAccuracy).toBeNull();
  expect(unlabeled.measuredMetrics.aiGain).toBeNull();
  expect(unlabeled.measuredMetrics.averageConfidence).toBe(0);
  trial.lines[0].groundTruth = 'xin chào';
  const labeled = JSON.parse(exportTrialToJson(store.computeTrialAnalytics(trial, true)));
  expect(labeled.measuredMetrics.rawAccuracy).toBe(0);
  expect(labeled.measuredMetrics.finalAccuracy).toBe(100);
  expect(labeled.measuredMetrics.aiAccuracy).toBe(0);
  expect(labeled.measuredMetrics.aiGain).toBe(0);
  expect(labeled.lines[0].confidenceSource).toBe('CRNN_CTC_SOFTMAX');
});
