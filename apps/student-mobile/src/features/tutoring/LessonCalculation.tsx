import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Svg, { Defs, Pattern, Path, Rect } from 'react-native-svg';
import { MathText } from '../../components/domain/MathText';
import { FONTS } from '../../constants/theme';

/** Present the supplied operation only; answers remain checked by the tutor service. */
export function LessonCalculation({ expression }: { expression: string }) {
  const column = /^(\d{1,6})\s*([+−-])\s*(\d{1,6})$/.exec(expression.trim());
  return <View style={styles.paper}>
    <Svg width="100%" height="100%" style={StyleSheet.absoluteFill} accessible={false}>
      <Defs><Pattern id="lesson-paper-grid" width="22" height="22" patternUnits="userSpaceOnUse"><Path d="M22 0H0V22" fill="none" stroke="#E8E0F4" strokeWidth="1" /></Pattern></Defs>
      <Rect width="100%" height="100%" fill="url(#lesson-paper-grid)" />
    </Svg>
    {column ? <View style={styles.operation} accessible accessibilityLabel={expression + ' bằng bao nhiêu?'}>
      <Text style={styles.digits}>{column[1]}</Text><View style={styles.addend}><Text style={styles.sign}>{column[2]}</Text><Text style={styles.digits}>{column[3]}</Text></View>
      <View style={styles.rule} /><Text style={styles.question}>?</Text>
    </View> : <MathText style={styles.math}>{expression + ' = ?'}</MathText>}
  </View>;
}
const styles = StyleSheet.create({
  paper: { position: 'relative', overflow: 'hidden', minHeight: 140, padding: 14, borderRadius: 17, borderWidth: 1, borderColor: '#EBE3F6', backgroundColor: '#FCFAFF', alignItems: 'center', justifyContent: 'center' },
  operation: { minWidth: 100, gap: 2 }, digits: { fontFamily: FONTS.bold, fontVariant: ['tabular-nums'], fontSize: 27, lineHeight: 35, textAlign: 'right', color: '#59437D', letterSpacing: 4 },
  addend: { flexDirection: 'row', justifyContent: 'space-between', gap: 16 }, sign: { fontFamily: FONTS.bold, fontSize: 27, lineHeight: 35, color: '#9A70DC' },
  rule: { height: 2, backgroundColor: '#B69BD9', marginTop: 3 }, question: { fontFamily: FONTS.extraBold, fontSize: 29, lineHeight: 38, color: '#8A56EF', textAlign: 'right' },
  math: { fontFamily: FONTS.extraBold, fontSize: 24, lineHeight: 34, color: '#7549CA' },
});
