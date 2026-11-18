import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import type { TrainingGameId } from '@mathvisionkid/training-games';
import { FONTS } from '../../constants/theme';

export const GAME_COVERS = {
  'star-quest': require('../../../assets/illustrations/games/star-quest.webp'),
  'race-to-finish': require('../../../assets/illustrations/games/race-to-finish.webp'),
  'terrain-racing': require('../../../assets/illustrations/games/terrain-racing.webp'),
  'energy-defense': require('../../../assets/illustrations/games/energy-defense.webp'),
  'planet-rescue': require('../../../assets/illustrations/games/planet-rescue.webp'),
  'block-island': require('../../../assets/illustrations/games/block-island.webp'),
} as const;

export function GameCover({ id, title }: { id: TrainingGameId | 'star-quest'; title: string }) {
  return <View style={styles.cover}>
    <Image source={GAME_COVERS[id]} style={StyleSheet.absoluteFill} contentFit="cover" accessible={false} transition={0} />
    <LinearGradient colors={['transparent', '#24104CDA']} locations={[0.3, 1]} style={StyleSheet.absoluteFill} pointerEvents="none" />
    <View style={styles.caption}>
      <Text accessibilityRole="header" style={styles.title}>{title}</Text>
      <View style={styles.play}><Ionicons name="play" size={16} color="#6745CF" accessible={false} /></View>
    </View>
  </View>;
}

const styles = StyleSheet.create({
  cover: { width: '100%', aspectRatio: 16 / 9, overflow: 'hidden', borderRadius: 23, backgroundColor: '#473080' },
  caption: { position: 'absolute', bottom: 14, left: 16, right: 14, flexDirection: 'row', alignItems: 'center', gap: 12 },
  title: { flex: 1, minWidth: 0, fontFamily: FONTS.extraBold, fontSize: 20, lineHeight: 27, color: '#FFFFFF' },
  play: { width: 34, height: 34, borderRadius: 17, backgroundColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center' },
});
