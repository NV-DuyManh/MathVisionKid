import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { COLORS, FONTS } from '../../constants/theme';

export type TaskProgressProps = { steps: readonly string[]; activeStep?: number; complete?: boolean };

/** Counts completed tasks, never estimated elapsed time or a guessed server percentage. */
export function TaskProgress({ steps, activeStep = 0, complete = false }: TaskProgressProps) {
  if (!steps.length) return null;
  const current = Number.isFinite(activeStep) ? Math.min(steps.length - 1, Math.max(0, Math.floor(activeStep))) : 0;
  const summary = complete ? 'Đã sẵn sàng' : `Bước ${current + 1}/${steps.length} · ${steps[current]}`;
  return <View style={styles.stack}>
    <View style={styles.segments} accessibilityRole="progressbar" accessibilityLabel="Tiến độ chuẩn bị"
      accessibilityState={{ busy: !complete }} aria-busy={!complete}
      accessibilityValue={{ min: 0, max: steps.length, now: complete ? steps.length : current, text: summary }}
      aria-valuemin={0} aria-valuemax={steps.length} aria-valuenow={complete ? steps.length : current} aria-valuetext={summary}>
      {steps.map((step, index) => <View key={`${index}:${step}`} style={[styles.segment,
        (complete || index < current) && styles.segmentDone, !complete && index === current && styles.segmentCurrent]} />)}
    </View>
    <View style={styles.list} accessibilityLiveRegion="polite">
      {steps.map((step, index) => {
        const done = complete || index < current, working = !complete && index === current;
        const status = done ? 'Đã xong' : working ? 'Đang làm' : 'Sắp tới';
        return <View key={`${index}:${step}`} style={styles.row} accessible accessibilityLabel={`${step}. ${status}`}>
          <View style={[styles.number, done && styles.numberDone, working && styles.numberCurrent]}>
            {done ? <Text style={styles.check} accessible={false}>✓</Text>
              : <Text style={[styles.numberText, working && styles.activeText]}>{index + 1}</Text>}
          </View>
          <Text style={[styles.name, (done || working) && styles.activeText]}>{step}</Text>
          <Text style={[styles.status, working && styles.activeText]}>{status}</Text>
        </View>;
      })}
    </View>
  </View>;
}

const styles = StyleSheet.create({
  stack: { width: '100%', gap: 12 }, segments: { flexDirection: 'row', gap: 7 },
  segment: { flex: 1, height: 8, borderRadius: 4, backgroundColor: '#E9E3FC' },
  segmentDone: { backgroundColor: '#7754F4' }, segmentCurrent: { backgroundColor: '#C4B2FF', borderColor: '#7754F4', borderWidth: 1 },
  list: { gap: 8 }, row: { flexDirection: 'row', alignItems: 'center', gap: 10, minHeight: 34 },
  number: { width: 26, height: 26, borderRadius: 13, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F0ECF8' },
  numberDone: { backgroundColor: '#7754F4' }, numberCurrent: { backgroundColor: '#E6DCFF', borderColor: '#7754F4', borderWidth: 1.5 },
  numberText: { fontFamily: FONTS.bold, fontSize: 12, color: COLORS.textMuted },
  check: { fontFamily: FONTS.bold, fontSize: 15, color: '#FFF' },
  name: { flex: 1, fontFamily: FONTS.semiBold, fontSize: 13, lineHeight: 20, color: COLORS.textMuted },
  status: { fontFamily: FONTS.medium, fontSize: 11, lineHeight: 17, color: COLORS.textMuted, maxWidth: '30%', flexShrink: 1, textAlign: 'right' },
  activeText: { color: COLORS.primaryDark },
});
