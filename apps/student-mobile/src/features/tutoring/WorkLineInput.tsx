import React, { useState } from 'react';
import { StyleSheet, Text, TextInput, View } from 'react-native';
import type { TextInputInstance, TextInputProps } from 'react-native';
import { COLORS, FONTS } from '../../constants/theme';

const FRACTION = /(?<![\w/.,])(?:\(\s*([+-]?\d+)\s*\)\s*[/⁄]\s*\(\s*(\d+)\s*\)|\\(?:d?frac)\s*\{\s*([+-]?\d+)\s*\}\s*\{\s*(\d+)\s*\}|([+-]?\d+)\s*[/⁄]\s*(\d+))(?![\w/]|[.,]\d)/g;

type Part = { text: string; hidden?: boolean } | { original: string; top: string; bottom: string; edited?: boolean };

function splitLine(source: string): Part[] {
  const parts: Part[] = [];
  let end = 0;
  for (const match of source.matchAll(FRACTION)) {
    parts.push({ text: source.slice(end, match.index), hidden: match.index === 0 }, {
      original: match[0], top: match[1] ?? match[3] ?? match[5], bottom: match[2] ?? match[4] ?? match[6],
    });
    end = match.index + match[0].length;
  }
  return [...parts, { text: source.slice(end), hidden: end === source.length }];
}

type Props = {
  value: string; label: string; disabled: boolean;
  inputRef?: React.Ref<TextInputInstance>; onChange: (value: string) => void;
};

function LinePartInput({ inputRef, centered, value, ...props }: TextInputProps & {
  inputRef?: Props['inputRef']; centered?: boolean;
}) {
  const [focused, setFocused] = useState(false);
  return <View style={[styles.part, centered && styles.numberPart]}>
    <Text aria-hidden accessibilityElementsHidden importantForAccessibility="no-hide-descendants"
      numberOfLines={1} style={[styles.partText, centered && styles.fractionText, styles.measure]}>{(value || '0').replace(/ /g, '\u00a0')}</Text>
    <TextInput {...props} ref={inputRef} value={value} underlineColorAndroid="transparent"
      onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
      style={[styles.partText, centered && styles.fractionText, styles.partInput, centered && styles.centered, focused && styles.focused]} />
  </View>;
}

export function WorkLineInput({ value, label, disabled, inputRef, onChange }: Props) {
  const [parts, setParts] = useState(() => splitLine(value));
  const formatFractions = () => {
    if (!value.includes('[?]')) setParts(splitLine(value));
  };
  if (parts.length === 1) return <TextInput ref={inputRef} accessibilityLabel={label} value={value} maxLength={500}
    editable={!disabled} onChangeText={onChange} onEndEditing={formatFractions} style={[styles.frame, styles.wholeLine]} />;

  const update = (index: number, part: Part) => {
    const next = parts.map((item, offset) => offset === index ? part : item);
    setParts(next);
    onChange(next.map(item => 'text' in item ? item.text : !item.edited ? item.original
      : /^[+-]?\d+$/.test(item.top) && /^[1-9]\d*$/.test(item.bottom)
        ? `${item.top}/${item.bottom}` : '[?]').join(''));
  };

  return (
    <View style={[styles.frame, styles.expression]} testID="work-line-expression">
      {parts.map((part, index) => {
        if ('text' in part) return part.hidden ? null : (
          <LinePartInput key={index} inputRef={index === 0 ? inputRef : undefined}
            accessibilityLabel={`${label}, phần ${index / 2 + 1}`} value={part.text} maxLength={500} editable={!disabled}
            onEndEditing={formatFractions}
            onChangeText={text => update(index, { text })} />
        );
        const number = Math.ceil(index / 2);
        return <View key={index} style={styles.fraction} testID="work-line-fraction">
          <LinePartInput centered inputRef={index === 1 && 'text' in parts[0] && parts[0].hidden ? inputRef : undefined}
            accessibilityLabel={`${label}, tử số ${number}`}
            value={part.top} keyboardType="numbers-and-punctuation" maxLength={14} editable={!disabled}
            onChangeText={top => update(index, { ...part, top, edited: true })} />
          <View style={styles.bar} />
          <LinePartInput centered accessibilityLabel={`${label}, mẫu số ${number}`}
            value={part.bottom} keyboardType="number-pad" maxLength={14} editable={!disabled}
            onChangeText={bottom => update(index, { ...part, bottom, edited: true })} />
        </View>;
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  frame: { paddingHorizontal: 10, borderWidth: 1, borderColor: COLORS.primaryDark,
    borderRadius: 10, backgroundColor: COLORS.surfaceSubdued },
  wholeLine: { minHeight: 48, fontSize: 17, color: COLORS.textPrimary, fontFamily: FONTS.regular },
  expression: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', columnGap: 2, rowGap: 4, paddingVertical: 8 },
  part: { minWidth: 12, maxWidth: '100%', minHeight: 24, justifyContent: 'center' },
  numberPart: { minWidth: 22, minHeight: 20 },
  partText: { fontSize: 17, lineHeight: 24, color: COLORS.textPrimary, fontFamily: FONTS.regular },
  fractionText: { fontSize: 15, lineHeight: 19 },
  measure: { paddingHorizontal: 4, opacity: 0 },
  partInput: { position: 'absolute', top: 0, bottom: 0, left: 0, right: 0,
    paddingHorizontal: 2, paddingVertical: 0, borderBottomWidth: 1, borderColor: 'transparent', includeFontPadding: false },
  focused: { borderColor: COLORS.primaryDark },
  centered: { textAlign: 'center' },
  fraction: { maxWidth: '100%' },
  bar: { height: 1.5, marginHorizontal: 2, marginVertical: 1, backgroundColor: COLORS.textPrimary },
});
