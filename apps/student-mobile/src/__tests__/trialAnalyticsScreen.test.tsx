import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { ActivityIndicator, Text } from 'react-native';
import RecognitionTrialAnalyticsScreen from '../app/recognition/trial-analytics';

let mockParams = { trialId: 'trial-a' };
const mockStore = {
  init: jest.fn(), getCurrentTrialAnalytics: jest.fn(), getSessions: () => [],
};
jest.mock('expo-router', () => ({ useLocalSearchParams: () => mockParams }));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
jest.mock('../components/ui/AppHeader', () => ({ AppHeader: 'AppHeader' }));
jest.mock('../components/ui/AppButton', () => ({ AppButton: 'AppButton' }));
jest.mock('../features/recognition/components/RecognitionSummary', () => ({ RecognitionSummary: 'RecognitionSummary' }));
jest.mock('../features/recognition/analytics/recognitionAnalyticsStore', () => ({
  recognitionAnalyticsStore: {
    init: () => mockStore.init(),
    getCurrentTrialAnalytics: (id: string) => mockStore.getCurrentTrialAnalytics(id),
    getSessions: () => mockStore.getSessions(),
  },
}));

test('returning to an earlier trial while another loads waits for fresh analytics', async () => {
  const trial = (text: string) => ({ totalLines: 1, status: 'COMPLETED', lineMetrics: [{ lineId: text, ocrOutput: text, finalResult: text }] });
  mockStore.init.mockResolvedValue(undefined);
  mockStore.getCurrentTrialAnalytics.mockResolvedValueOnce(trial('Kết quả A cũ'));
  let renderer!: TestRenderer.ReactTestRenderer;
  await act(async () => { renderer = TestRenderer.create(<RecognitionTrialAnalyticsScreen />); });
  const text = () => renderer.root.findAllByType(Text).map(node => String(node.props.children)).join(' ');
  expect(text()).toContain('Kết quả A cũ');
  let finishB!: (value: ReturnType<typeof trial>) => void;
  mockStore.getCurrentTrialAnalytics.mockImplementationOnce(() => new Promise(resolve => { finishB = resolve; }));
  mockParams = { trialId: 'trial-b' };
  await act(async () => renderer.update(<RecognitionTrialAnalyticsScreen />));
  let finishFreshA!: (value: ReturnType<typeof trial>) => void;
  mockStore.getCurrentTrialAnalytics.mockImplementationOnce(() => new Promise(resolve => { finishFreshA = resolve; }));
  mockParams = { trialId: 'trial-a' };
  await act(async () => renderer.update(<RecognitionTrialAnalyticsScreen />));
  try {
    expect(renderer.root.findAllByType(ActivityIndicator)).toHaveLength(1);
    expect(text()).not.toContain('Kết quả A cũ');
    await act(async () => finishB(trial('Kết quả B')));
    expect(renderer.root.findAllByType(ActivityIndicator)).toHaveLength(1);
    await act(async () => finishFreshA(trial('Kết quả A mới')));
    expect(text()).toContain('Kết quả A mới');
    expect(text()).not.toContain('Kết quả B');
    expect(renderer.root.findAllByType(ActivityIndicator)).toHaveLength(0);
  } finally {
    act(() => renderer.unmount());
  }
});
