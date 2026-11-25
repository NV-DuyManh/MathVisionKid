import React from 'react';
import { Image, View, type ImageSourcePropType } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export function ApprovedEmblem({ source, size = 76, unlocked = true }: {
  source?: ImageSourcePropType; size?: number; unlocked?: boolean;
}) {
  // Use the transparent derived art, keeping its aspect ratio and glow.
  const lockSize = Math.max(14, Math.round(size * .28));
  return <View accessible={false} aria-hidden style={{ width: size, height: size, flexShrink: 0, justifyContent: 'center', alignItems: 'center' }}>
    {!source && <Ionicons name="shield-outline" size={size * .7} color="#8593A9" accessible={false} />}
    {source && <Image testID="approved-emblem-image" source={source} resizeMode="contain" accessible={false}
      style={{ width: size, height: size, opacity: unlocked ? 1 : .65 }} />}
    {!unlocked && <View testID="approved-emblem-lock" style={{ position: 'absolute', right: 0, bottom: 0, width: lockSize, height: lockSize,
      borderRadius: lockSize / 2, backgroundColor: '#40345D', borderColor: '#FFFFFF', borderWidth: 1, justifyContent: 'center', alignItems: 'center' }}>
      <Ionicons name="lock-closed" size={lockSize * .61} color="#FFFFFF" accessible={false} />
    </View>}
  </View>;
}
