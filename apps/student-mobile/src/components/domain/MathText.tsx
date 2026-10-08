import React from 'react';
import { StyleProp, StyleSheet, Text, TextStyle, View } from 'react-native';

/** Slash fractions are presentation only; the source text and answer API stay literal. */
export function MathText({ children, style }: { children: string; style?: StyleProp<TextStyle> }) {
  const parts = children.split(/(?<![\w/.,])(\d+\s*\/\s*[1-9]\d*)(?![\w/]|[.,]\d)/g);
  if (parts.length === 1) return <Text style={style}>{children}</Text>;
  const textStyle = StyleSheet.flatten(style) || {};
  const size = textStyle.fontSize || 16;
  const spoken = children.replace(/(?<![\w/.,])(\d+)\s*\/\s*([1-9]\d*)(?![\w/]|[.,]\d)/g, '$1 phần $2');
  return <View style={styles.flow} accessible accessibilityLabel={spoken}>
    {parts.flatMap((part, index) => {
      if (index % 2) {
        const [top, bottom] = part.split('/').map(value => value.trim());
        return [<View key={`fraction-${index}`} testID="stacked-fraction" style={styles.fraction} accessible={false}>
          <Text style={[style, { fontSize: size * .86, lineHeight: size * 1.05, textAlign: 'center' }]}>{top}</Text>
          <View style={[styles.bar, { backgroundColor: textStyle.color || '#171044' }]} />
          <Text style={[style, { fontSize: size * .86, lineHeight: size * 1.05, textAlign: 'center' }]}>{bottom}</Text>
        </View>];
      }
      return (part.match(/\n|[^\s]+[^\S\n]*|[^\S\n]+/g) || []).map((word, token) => word === '\n'
        ? <View key={`${index}-${token}`} style={styles.newline} />
        : <Text key={`${index}-${token}`} style={[style, styles.word]} accessible={false}>{word}</Text>);
    })}
  </View>;
}

const styles = StyleSheet.create({
  flow: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', rowGap: 4 },
  word: { maxWidth: '100%' },
  fraction: { alignItems: 'stretch', marginHorizontal: 3, paddingHorizontal: 2, minWidth: 18 },
  bar: { height: 1.5, minWidth: 18, marginVertical: 1 },
  newline: { width: '100%', height: 0 },
});
