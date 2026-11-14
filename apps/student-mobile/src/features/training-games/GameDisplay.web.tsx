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

export function GameDisplay({ gameId, children, onExit }: { gameId: TrainingGameId; children: React.ReactNode; onExit?: () => void }) {
  const { width, height } = useWindowDimensions();
  const portraitPhone = trainingScreenOptions(gameId).orientation === 'landscape' && width < 700 && height > width;
  // Mount the board once in landscape. Keeping it mounted after that preserves
  // the current race if the player briefly rotates the phone back to portrait.
  const [opened, setOpened] = React.useState(!portraitPhone);
  if (!opened && !portraitPhone) setOpened(true);
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
    {opened && <View aria-hidden={portraitPhone || undefined} style={portraitPhone ? styles.hidden : styles.root}>{children}</View>}
  </View>;
}
const styles = StyleSheet.create({
  root: { flex: 1, minHeight: 0 },
  hidden: { display: 'none' },
  notice: { flex: 1, padding: 24, gap: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.primaryLight },
  title: { fontFamily: FONTS.extraBold, fontSize: 24, color: COLORS.textPrimary },
  text: { maxWidth: 350, fontFamily: FONTS.semiBold, fontSize: 16, textAlign: 'center', color: COLORS.textPrimary },
  button: { minHeight: 48, justifyContent: 'center', paddingHorizontal: 16, borderRadius: 12, backgroundColor: COLORS.primary },
  buttonText: { fontFamily: FONTS.bold, fontSize: 14, color: '#FFFFFF' },
});
