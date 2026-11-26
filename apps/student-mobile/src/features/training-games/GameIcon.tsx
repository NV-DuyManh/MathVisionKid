import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Image, type ImageSource } from 'expo-image';

export type GameArtwork = { id: string; source: ImageSource | number };

// Static imports let Metro and the web export fingerprint/bundle each thumbnail.
// No remote image request or gameplay entry is needed by the catalog.
export const GAME_ARTWORK = {
  'star-quest': { id: 'star-quest', source: require('../../../assets/game-artwork/star-quest.webp') },
  'race-to-finish': { id: 'race-to-finish', source: require('../../../assets/game-artwork/race-to-finish.webp') },
  'terrain-racing': { id: 'terrain-racing', source: require('../../../assets/game-artwork/terrain-racing.webp') },
  'energy-defense': { id: 'energy-defense', source: require('../../../assets/game-artwork/energy-defense.webp') },
  'planet-rescue': { id: 'planet-rescue', source: require('../../../assets/game-artwork/planet-rescue.webp') },
  'block-island': { id: 'block-island', source: require('../../../assets/game-artwork/block-island.webp') },
} satisfies Record<string, GameArtwork>;

export function GameIcon({ artwork, size = 64 }: { artwork: GameArtwork; size?: number }) {
  return <View accessible={false} importantForAccessibility="no-hide-descendants" aria-hidden
    pointerEvents="none" style={[styles.tile, { width: size, height: size, borderRadius: size * .28 }]}>
    <Image testID={`game-artwork-${artwork.id}`} source={artwork.source} contentFit="contain"
      accessible={false} transition={0} style={StyleSheet.absoluteFill} />
  </View>;
}
const styles = StyleSheet.create({
  tile: { flexShrink: 0, overflow: 'hidden', backgroundColor: '#EDE8F4' },
});
