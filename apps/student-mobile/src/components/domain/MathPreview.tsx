import React, { useState } from 'react';
import { StyleProp, StyleSheet, TextStyle, View } from 'react-native';
import { MathText } from './MathText';

/** A complete-token preview keeps fraction bars and denominators together. */
export function MathPreview({ children, style }: { children: string; style?: StyleProp<TextStyle> }) {
  const [width, setWidth] = useState(0);
  const size = StyleSheet.flatten(style)?.fontSize || 12;
  const normalized = children.replace(/\\(?:d?frac)\s*\{\s*([+−-]?\d+)\s*\}\s*\{\s*([1-9]\d*)\s*\}/g, '$1/$2')
    .replace(/\(\s*([+-]?\d+)\s*\)\s*[/⁄]\s*\(\s*([1-9]\d*)\s*\)/g, '$1/$2');
  const tokens = normalized.match(/[+−-]?\d+\s*[/⁄]\s*[1-9]\d*|\S+/g) || [];
  const selected: string[] = [];
  let used = size * 1.5;
  for (const token of tokens) {
    const estimate = token.includes('/') ? size * 2.2 : [...token].length * size * .68;
    if (used + estimate > width) break;
    selected.push(token);
    used += estimate + size * .4;
  }
  return <View onLayout={event => setWidth(event.nativeEvent.layout.width)} style={styles.container}>
    <MathText style={style}>{selected.join(' ') + (selected.length < tokens.length ? '…' : '')}</MathText>
  </View>;
}

const styles = StyleSheet.create({ container: { width: '100%', minHeight: 30, justifyContent: 'center' } });
