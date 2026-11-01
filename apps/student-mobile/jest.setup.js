// Native font files are represented by asset IDs in Jest, not device resources.
// Browser/export checks exercise the real font loader separately.
const { jest } = require('@jest/globals');
jest.mock('@react-native-async-storage/async-storage', () => require('@react-native-async-storage/async-storage/jest/async-storage-mock'));

jest.mock('expo-font', () => ({
  ...jest.requireActual('expo-font'),
  isLoaded: jest.fn(() => true),
  loadAsync: jest.fn(async () => {}),
}));
