import React from 'react';
import { StyleProp, StyleSheet, Text, TextStyle, View } from 'react-native';

/** Slash fractions are presentation only; the source text and answer API stay literal. */
export function MathText({ children, style }: { children: string; style?: StyleProp<TextStyle> }) {
  // OCR may preserve the grouping around each printed numerator/denominator.
  // Normalize presentation only; keep the original source for confirmation/API use.
  const protectedParts = children.split(/((?:https?:\/\/|www\.)\S+|(?<!\S)(?:[A-Za-z]:[\\/]|\/)[^\s]+)/g);
  const displayed = protectedParts.map((part, index) => index % 2 ? part : part
    .replace(/\\(?:[()[\]]|left|right)/g, '')
    .replace(/\\(?:times|cdot)\b/g, '×').replace(/\\div\b/g, '÷')
    .replace(/\\(?:d?frac)\s*\{\s*([+−-]?\d+)\s*\}\s*\{\s*([1-9]\d*)\s*\}/g, '$1/$2')
    .replace(/\(\s*([+-]?\d+)\s*\)\s*[/⁄]\s*\(\s*([1-9]\d*)\s*\)/g, '$1/$2')
    .replace(/⁄/g, '/').replace(/\*\*([^*]+)\*\*/g, '$1')).join('');
  const fractionPattern = /(?<![\w/.,])([+−-]?\d+\s*\/\s*[1-9]\d*)(?![\w/]|[.,]\d)/g;
  const parts = displayed.split(/((?:https?:\/\/|www\.)\S+|(?<!\S)(?:[A-Za-z]:[\\/]|\/)[^\s]+)/g)
    .flatMap((part, index) => index % 2 ? [{ text: part, fraction: false }] : part.split(fractionPattern).map((text, token) => ({ text, fraction: token % 2 === 1 })));
  if (!parts.some(part => part.fraction)) return <Text style={style}>{displayed}</Text>;
  const textStyle = StyleSheet.flatten(style) || {};
  const size = textStyle.fontSize || 16;
  const spoken = parts.map(part => part.fraction ? part.text.replace(/\s*\/\s*/, ' phần ') : part.text).join('');
  return <View style={styles.flow} accessible accessibilityLabel={spoken}>
    {parts.flatMap(({ text: part, fraction }, index) => {
      if (fraction) {
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
