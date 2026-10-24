import React, { Component, Suspense, lazy, useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { usePreventRemove } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { TrainingServicesContext, type TrainingGameId } from '@mathvisionkid/training-games';
import { COLORS, FONTS } from '../../constants/theme';
import { createTrainingRuntime } from './runtime';
import { trainingResults } from './resultStore';
import { trainingTrace } from './diagnostics';
import { loadTrainingGame } from './gameEntries';
import { trainingStatusBarHidden } from './presentation';
import { useTrainingNativeDiagnostics } from './nativeDiagnostics';

const GAMES = {
  'planet-rescue': lazy(() => loadTrainingGame('planet-rescue')),
  'race-to-finish': lazy(() => loadTrainingGame('race-to-finish')),
  'terrain-racing': lazy(() => loadTrainingGame('terrain-racing')),
  'energy-defense': lazy(() => loadTrainingGame('energy-defense')),
  'block-island': lazy(() => loadTrainingGame('block-island')),
};
export function GameFallback({ message, onBack }: { message: string; onBack: () => void }) {
  return <View style={styles.fallback}><Text style={styles.message}>{message}</Text><Pressable accessibilityRole="button" accessibilityLabel="Trở về danh sách game" onPress={onBack} style={styles.button}><Text style={styles.buttonText}>Trở về danh sách game</Text></Pressable></View>;
}
class GameBoundary extends Component<{ children: React.ReactNode; onBack: () => void; onFailure: () => void }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch() { this.props.onFailure(); }
  render() { return this.state.failed ? <GameFallback message="Trò chơi chưa mở được. Em quay lại để thử trò khác nhé." onBack={this.props.onBack} /> : this.props.children; }
}
function GameEntry({ Game, gameId, trial, onExit }: { Game: React.ComponentType<{ onExit: () => void }>; gameId: TrainingGameId; trial: boolean; onExit: () => void }) {
  useEffect(() => {
    trainingTrace('game-mounted', { gameId, mode: trial ? 'trial' : 'student' });
    return () => trainingTrace('game-unmounted', { gameId, mode: trial ? 'trial' : 'student' });
  }, [gameId, trial]);
  return <Game onExit={onExit} />;
}
export function GamePlayer({ studentId, gameId, trial = false, onExit }: { studentId: string; gameId: TrainingGameId; trial?: boolean; onExit: () => void }) {
  return <TrainingGameSession key={`${studentId}:${gameId}:${trial}`} studentId={studentId} trial={trial} gameId={gameId} onExit={onExit} Game={GAMES[gameId]} />;
}
export function TrainingGameSession({ studentId, gameId, trial = false, onExit, Game }: { studentId: string; gameId: TrainingGameId; trial?: boolean; onExit: () => void; Game: React.ComponentType<{ onExit: () => void }> }) {
  useTrainingNativeDiagnostics(gameId, trial);
  const [runtime, setRuntime] = useState<ReturnType<typeof createTrainingRuntime> | null>(null);
  const runtimeOwner = useRef<ReturnType<typeof createTrainingRuntime> | null>(null);
  const alive = useRef(false), exitRequested = useRef(false), exitDelivered = useRef(false);
  const [statusBar, setStatusBar] = useState<{ owner: ReturnType<typeof createTrainingRuntime>; hidden: boolean } | null>(null);
  const [settingsError, setSettingsError] = useState<{ owner: ReturnType<typeof createTrainingRuntime>; message: string | null } | null>(null);
  const activeRuntime = runtime?.studentId === studentId && runtime.gameId === gameId && runtime.trial === trial ? runtime : null;
  const currentSettingsError = settingsError?.owner === activeRuntime ? settingsError.message : null;
  const [leaving, setLeaving] = useState(false);
  const [failed, setFailed] = useState(false);
  const error = useSyncExternalStore(trainingResults.subscribe, () => trial ? null : trainingResults.error(studentId), () => null);
  const requestExit = useCallback(() => {
    if (!alive.current || exitRequested.current || (runtime && runtimeOwner.current !== runtime)) return;
    exitRequested.current = true; runtimeOwner.current?.dispose(); setLeaving(true);
  }, [runtime]);
  usePreventRemove(gameId !== 'race-to-finish' && !leaving && !failed, () => { if (!activeRuntime?.requestBack()) requestExit(); });
  useEffect(() => { if (leaving && !exitDelivered.current) { exitDelivered.current = true; onExit(); } }, [leaving, onExit]);
  useEffect(() => {
    // Each effect setup owns its runtime, including StrictMode's setup/cleanup replay.
    let active = true;
    alive.current = true;
    const next = createTrainingRuntime(studentId, gameId, trial,
      hidden => { if (active) setStatusBar({ owner: next, hidden }); },
      message => { if (active) setSettingsError({ owner: next, message }); });
    runtimeOwner.current = next;
    void next.ready.then(() => { if (active) setRuntime(next); });
    return () => { active = false; alive.current = false; if (runtimeOwner.current === next) runtimeOwner.current = null; next.dispose(); };
  }, [studentId, gameId, trial]);
  return <GestureHandlerRootView style={styles.root} testID={`training-player-${gameId}`}>
    {activeRuntime && !leaving && !failed && <StatusBar style="dark" hidden={statusBar?.owner === activeRuntime ? statusBar.hidden : trainingStatusBarHidden(gameId)} />}
    {trial && <Text accessibilityRole="alert" style={styles.errorText}>Chơi thử · Không lưu thành tích</Text>}
    {(error || currentSettingsError) && <View accessibilityRole="alert" style={styles.error}><Text style={styles.errorText}>{error ?? currentSettingsError}</Text>{error && <Pressable accessibilityRole="button" accessibilityLabel="Thử lưu kết quả" onPress={() => { void trainingResults.retry(studentId).catch(() => {}); }}><Text style={styles.errorText}>Thử lưu lại</Text></Pressable>}</View>}
    <GameBoundary onBack={requestExit} onFailure={() => { trainingTrace('game-error', { gameId, mode: trial ? 'trial' : 'student' }); runtime?.dispose(); setFailed(true); }}>
      {activeRuntime ? <TrainingServicesContext.Provider value={activeRuntime.services}>
        <Suspense fallback={<View style={styles.fallback}><ActivityIndicator color={COLORS.primary} /><Text style={styles.message}>Đang mở trò chơi…</Text><Pressable accessibilityRole="button" onPress={requestExit}><Text style={styles.message}>Quay lại</Text></Pressable></View>}>
          {!leaving && <GameEntry Game={Game} gameId={gameId} trial={trial} onExit={requestExit} />}
        </Suspense>
      </TrainingServicesContext.Provider> : <View style={styles.fallback}><ActivityIndicator color={COLORS.primary} /><Text style={styles.message}>Đang chuẩn bị trò chơi của em…</Text><Pressable accessibilityRole="button" accessibilityLabel="Trở về danh sách game" onPress={requestExit} style={styles.button}><Text style={styles.buttonText}>Quay lại</Text></Pressable></View>}
    </GameBoundary>
  </GestureHandlerRootView>;
}
const styles = StyleSheet.create({ root: { flex: 1, minHeight: 0 }, fallback: { flex: 1, padding: 24, gap: 20, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.background }, message: { fontFamily: FONTS.bold, fontSize: 17, color: COLORS.textPrimary, textAlign: 'center' }, button: { minHeight: 48, padding: 16, backgroundColor: COLORS.primary, borderRadius: 20 }, buttonText: { fontFamily: FONTS.bold, color: '#FFFFFF' }, error: { padding: 10, backgroundColor: COLORS.warningLight }, errorText: { fontFamily: FONTS.semiBold, color: '#7C4315' } });
