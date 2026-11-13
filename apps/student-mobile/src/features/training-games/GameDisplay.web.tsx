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

export function GameDisplay({ gameId, children }: { gameId: TrainingGameId; children: React.ReactNode }) {
  const { width, height } = useWindowDimensions();
  const portraitPhone = trainingScreenOptions(gameId).orientation === 'landscape' && width < 700 && height > width;
  useEffect(() => {
    if (requestedGame !== gameId) enterGameDisplay(gameId);
    return () => {
      if (requestedGame !== gameId) return;
      requestedGame = undefined;
      ++generation;
      const exitFullscreen = ownsFullscreen && document.fullscreenElement === document.documentElement;
      ownsFullscreen = false;
      void (async () => {
        if (exitFullscreen) await document.exitFullscreen();
      })().catch(() => {});
      try { screen.orientation?.unlock?.(); } catch { /* Orientation controls may be blocked by the browser. */ }
    };
  }, [gameId]);
  return <View style={styles.root}>
    {portraitPhone ? <View style={styles.notice}>
      <Text style={styles.text}>Xoay ngang điện thoại để chơi rộng hơn.</Text>
      <Pressable accessibilityRole="button" accessibilityLabel="Mở trò chơi toàn màn hình và xoay ngang" onPress={() => enterGameDisplay(gameId)} style={styles.button}>
        <Text style={styles.buttonText}>Toàn màn hình</Text>
      </Pressable>
    </View> : null}
    {children}
  </View>;
}
const styles = StyleSheet.create({
  root: { flex: 1, minHeight: 0 },
  notice: { padding: 8, gap: 8, flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.primaryLight },
  text: { flex: 1, fontFamily: FONTS.semiBold, fontSize: 12, color: COLORS.textPrimary },
  button: { minHeight: 44, justifyContent: 'center', paddingHorizontal: 12, borderRadius: 12, backgroundColor: COLORS.primary },
  buttonText: { fontFamily: FONTS.bold, fontSize: 12, color: '#FFFFFF' },
});
