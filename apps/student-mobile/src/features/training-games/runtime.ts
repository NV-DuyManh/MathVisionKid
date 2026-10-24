import AsyncStorage from '@react-native-async-storage/async-storage';
import { AudioController, ProfileManager, QuestionHistory, ScopedGameStorage, TrainingSessionBridge, type TrainingGameId, type TrainingServices } from '@mathvisionkid/training-games';
import { trainingResults } from './resultStore';
import { trainingTrace } from './diagnostics';

let sequence = 0;
// QuestionHistory owns a persistence queue. Reopening a game must reuse that
// owner, so a delayed old write cannot replace a newer history for the same key.
const questionHistories = new Map<string, QuestionHistory>();
export function createTrainingRuntime(studentId: string, gameId: TrainingGameId, trial = false, onStatusBarHidden?: (hidden: boolean) => void) {
  if (trial && (!__DEV__ || !/^development-trial:\d+$/.test(studentId))) throw new Error('Trial runtime is development-only and cannot use a student UUID');
  const mountId = `${Date.now().toString(36)}-${(++sequence).toString(36)}-${Math.random().toString(36).slice(2)}`;
  let disposed = false;
  // Trial writes never reach AsyncStorage, host achievements or a network API.
  // Each mount owns its Map; late callbacks only hold that obsolete Map.
  const trialData = new Map<string, string>();
  const memory = {
    getItem: async (key: string) => disposed ? null : trialData.get(key) ?? null,
    setItem: async (key: string, value: string) => { if (!disposed) trialData.set(key, value); },
    removeItem: async (key: string) => { trialData.delete(key); },
    clear: async () => { trialData.clear(); },
  };
  const underlying = { getItem: (key: string) => AsyncStorage.getItem(key), setItem: (key: string, value: string) => AsyncStorage.setItem(key, value), removeItem: (key: string) => AsyncStorage.removeItem(key), clear: async () => { throw new Error('Global clear disabled'); } };
  const scoped = trial ? null : new ScopedGameStorage(underlying, studentId, gameId);
  const storage = scoped ?? memory;
  let history = scoped ? questionHistories.get(scoped.prefix) : undefined;
  if (!history) { history = new QuestionHistory(storage, 'questions:v1'); if (scoped) questionHistories.set(scoped.prefix, history); }
  let back: (() => void) | null = null;
  const storageError = () => { if (!trial) trainingResults.reportStorageError(studentId, gameId); };
  const bridge = new TrainingSessionBridge({ studentId, gameId, mountId,
    onResult: result => { if (!trial) void trainingResults.save(studentId, result).catch(() => {}); },
    onEvent: event => { if (!trial) void trainingResults.event(studentId, event).catch(() => {}); },
  });
  const profileManager = new ProfileManager(storage, studentId);
  const soundManager = new AudioController(enabled => {
    const write = gameId === 'terrain-racing' ? storage.setItem('terrain-sound:v1', JSON.stringify(enabled)) : profileManager.updateSettings({ soundEnabled: enabled });
    void write.catch(storageError);
  });
  const ready = (async () => {
    try {
      const profile = await profileManager.getOrCreateProfile();
      const terrainSound = gameId === 'terrain-racing' ? await storage.getItem('terrain-sound:v1') : null;
      if (!disposed) soundManager.setSoundEnabled(gameId === 'terrain-racing' ? terrainSound === 'true' : profile.settings.soundEnabled, false);
      if (!disposed) trainingTrace('runtime-ready', { gameId, mode: trial ? 'trial' : 'student' });
    } catch { storageError(); }
  })();
  const services: TrainingServices = {
    profileId: studentId, storage, profileManager,
    questionHistory: history, soundManager, bridge,
    setStatusBarHidden: hidden => { if (!disposed) onStatusBarHidden?.(hidden); },
    registerBack: handler => { if (disposed) return () => {}; back = handler; return () => { if (back === handler) back = null; }; },
  };
  return { studentId, gameId, trial, services, ready, requestBack: () => { if (disposed) return false; if (back) { back(); return true; } return false; },
    dispose: () => { if (disposed) return; disposed = true; bridge.dispose(); soundManager.dispose(); back = null; trialData.clear(); trainingTrace('runtime-disposed', { gameId, mode: trial ? 'trial' : 'student' }); },
  };
}
