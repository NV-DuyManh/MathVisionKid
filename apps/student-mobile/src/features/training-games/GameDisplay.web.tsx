import React, { useEffect } from 'react';
import { Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { COLORS, FONTS } from '../../constants/theme';
import type { TrainingGameId } from '@mathvisionkid/training-games';
import { trainingScreenOptions } from './presentation';

type GameOrientation = ScreenOrientation & { lock?: (direction: string) => Promise<void> };
let requestedGame: TrainingGameId | undefined;
let ownsFullscreen = false;
let generation = 0;

/** Start fullscreen within the play button's user gesture, before routing. */
export function enterGameDisplay(gameId: TrainingGameId) {
  if (typeof document === 'undefined' || !window.matchMedia?.('(pointer: coarse)').matches) return;
  const orientation = trainingScreenOptions(gameId).orientation;
  if (orientation === 'default') return;
  requestedGame = gameId;
  const current = ++generation;
  const root = document.documentElement;
  void (async () => {
    const opensFullscreen = !document.fullscreenElement && root.requestFullscreen;
    if (opensFullscreen) await root.requestFullscreen();
    if (current !== generation) {
      if (opensFullscreen && !requestedGame && document.fullscreenElement === root) await document.exitFullscreen();
      return;
    }
    if (opensFullscreen) ownsFullscreen = true;
    await (screen.orientation as GameOrientation)?.lock?.(orientation);
  })().catch(() => {});
}

export function cancelGameDisplay() {
  if (!requestedGame) return;
  requestedGame = undefined;
  ++generation;
  const exitFullscreen = ownsFullscreen && typeof document !== 'undefined' &&
    document.fullscreenElement === document.documentElement;
  ownsFullscreen = false;
  void (async () => {
    if (exitFullscreen) await document.exitFullscreen();
  })().catch(() => {});
  try { screen.orientation?.unlock?.(); } catch { /* Orientation controls may be blocked by the browser. */ }
}

export function GameDisplay({ gameId, children, onExit, pauseInPortrait }: {
  gameId: TrainingGameId; children: React.ReactNode; onExit?: () => void; pauseInPortrait?: boolean;
}) {
  const { width, height } = useWindowDimensions();
  const desktop = typeof window !== 'undefined' && window.matchMedia?.('(pointer: fine)').matches;
  // Terrain's world is designed in portrait coordinates (540 × 970). Give its
  // existing camera a proportional viewport instead of stretching the road.
  const portraitStage = desktop && gameId === 'terrain-racing'
    ? { width: Math.min(width, height * 540 / 970), alignSelf: 'center' as const } : undefined;
  const portraitPhone = trainingScreenOptions(gameId).orientation === 'landscape' && width < 700 && height > width;
  const canFullscreen = typeof document !== 'undefined' && !!document.documentElement.requestFullscreen &&
    !!window.matchMedia?.('(pointer: coarse)').matches && trainingScreenOptions(gameId).orientation !== 'default';
  const [fullscreenActive, setFullscreenActive] = React.useState(() => typeof document !== 'undefined' && !!document.fullscreenElement);
  useEffect(() => {
    if (typeof document === 'undefined') return;
    const update = () => setFullscreenActive(!!document.fullscreenElement);
    document.addEventListener?.('fullscreenchange', update);
    return () => document.removeEventListener?.('fullscreenchange', update);
  }, []);
  // Mount the board once in landscape. Keeping it mounted after that preserves
  // the current race if the player briefly rotates the phone back to portrait.
  const [opened, setOpened] = React.useState(!portraitPhone);
  if (!opened && !portraitPhone) setOpened(true);
  useEffect(() => {
    if (requestedGame !== gameId) enterGameDisplay(gameId);
    return () => {
      if (requestedGame !== gameId) return;
      cancelGameDisplay();
    };
  }, [gameId]);
  return <View style={[styles.root, gameId === 'terrain-racing' && styles.terrain]}>
    {portraitPhone ? <View style={styles.notice}>
      <Text accessibilityRole="header" style={styles.title}>Đua Về Đích</Text>
      <Text style={styles.text}>Xoay ngang điện thoại để xem đủ bàn đua và chọn nhân vật.</Text>
      <Pressable accessibilityRole="button" accessibilityLabel="Mở trò chơi toàn màn hình và xoay ngang"
        onPress={() => enterGameDisplay(gameId)} style={styles.button}>
        <Text style={styles.buttonText}>Toàn màn hình</Text>
      </Pressable>
      {onExit && <Pressable accessibilityRole="button" onPress={onExit} style={styles.button}>
        <Text style={styles.buttonText}>Về danh sách trò chơi</Text>
      </Pressable>}
    </View> : null}
    {opened && (!pauseInPortrait || !portraitPhone) &&
      <View aria-hidden={portraitPhone || undefined} style={portraitPhone ? styles.hidden : [styles.root, portraitStage]}>{children}</View>}
    {!portraitPhone && canFullscreen && !fullscreenActive && <Pressable accessibilityRole="button"
      accessibilityLabel="Mở trò chơi toàn màn hình" onPress={() => enterGameDisplay(gameId)} style={styles.fullscreenButton}>
      <Text style={styles.buttonText}>Toàn màn hình</Text>
    </Pressable>}
  </View>;
}
const styles = StyleSheet.create({
  root: { flex: 1, minHeight: 0 },
  terrain: { backgroundColor: '#142942' },
  hidden: { display: 'none' },
  notice: { flex: 1, padding: 24, gap: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.primaryLight },
  title: { fontFamily: FONTS.extraBold, fontSize: 24, color: COLORS.textPrimary },
  text: { maxWidth: 350, fontFamily: FONTS.semiBold, fontSize: 16, textAlign: 'center', color: COLORS.textPrimary },
  button: { minHeight: 48, justifyContent: 'center', paddingHorizontal: 16, borderRadius: 12, backgroundColor: COLORS.primary },
  buttonText: { fontFamily: FONTS.bold, fontSize: 14, color: '#FFFFFF' },
  fullscreenButton: { position: 'absolute', top: 8, right: 8, minHeight: 44, justifyContent: 'center', paddingHorizontal: 12, borderRadius: 12, backgroundColor: COLORS.primary },
});
