import React, { type ComponentProps } from 'react';
import { StyleSheet, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

type Glyph = ComponentProps<typeof Ionicons>['name'];
export type GameArtwork = { icon: Glyph; accent: Glyph; color: string; tint: string };

export function GameIcon({ artwork }: { artwork: GameArtwork }) {
  return <View accessible={false} importantForAccessibility="no-hide-descendants" aria-hidden
    style={[styles.tile, { backgroundColor: artwork.tint }]}>
    <Ionicons name={artwork.icon} size={34} color={artwork.color} style={styles.glyph} />
    <View style={[styles.accent, { backgroundColor: artwork.color }]}>
      <Ionicons name={artwork.accent} size={13} color="#FFFFFF" />
    </View>
  </View>;
}

const styles = StyleSheet.create({
  tile: { width: 64, height: 64, borderRadius: 19, flexShrink: 0, alignItems: 'center', justifyContent: 'center' },
  glyph: { transform: [{ rotate: '-8deg' }], marginRight: 4, marginBottom: 4 },
  accent: { position: 'absolute', bottom: 2, right: 2, width: 23, height: 23, borderRadius: 12,
    borderWidth: 2, borderColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center' },
});
