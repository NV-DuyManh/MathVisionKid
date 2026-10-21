import React from 'react';
import { StyleSheet, View } from 'react-native';
import Svg, { Circle, Path, Rect, Text as SvgText } from 'react-native-svg';
import { COLORS, FONTS } from '../../constants/theme';

export type FractionShapeKind = 'circle' | 'square' | 'bar';

type Props = {
  shape: FractionShapeKind;
  denominator: number;
  whole: number;
  selected: number[];
  onToggle: (index: number) => void;
};

const SIDE = 216;
const INSET = 12;
const CENTER = 120;
const RADIUS = 108;

export function FractionShape({ shape, denominator, whole, selected, onToggle }: Props) {
  const bar = shape === 'bar';
  // Use a rectangular grid when possible; prime denominators use equal strips.
  let rows = Math.floor(Math.sqrt(denominator));
  while (denominator % rows !== 0) rows--;
  const columns = denominator / rows;
  const height = bar ? 72 : SIDE;

  return <View style={[styles.frame, bar && styles.bar]}>
    {/* The large, named checkboxes below provide the same selection to assistive technology. */}
    <Svg width="100%" height="100%" viewBox={`0 0 240 ${bar ? 96 : 240}`}
      accessible={false} aria-hidden focusable={false} accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants" testID={`fraction-shape-${whole}`}>
      {Array.from({ length: denominator }, (_, part) => {
        const index = whole * denominator + part;
        const checked = selected.includes(index);
        const fill = checked ? COLORS.primaryDark : COLORS.surface;
        const stroke = checked ? COLORS.surface : COLORS.primaryDark;
        const regionProps = { fill, stroke, strokeWidth: 2, onPress: () => onToggle(index),
          testID: `fraction-region-${whole}-${part}`, accessible: false, focusable: false };
        let x: number;
        let y: number;
        let region: React.ReactNode;

        if (shape === 'circle') {
          const angle = Math.PI * 2 / denominator;
          const start = part * angle - Math.PI / 2;
          const end = start + angle;
          const point = (radians: number) => `${CENTER + RADIUS * Math.cos(radians)} ${CENTER + RADIUS * Math.sin(radians)}`;
          // One complete circle cannot be drawn with a single SVG arc whose endpoints coincide.
          region = denominator === 1
            ? <Circle key={part} {...regionProps} cx={CENTER} cy={CENTER} r={RADIUS} />
            : <Path key={part} {...regionProps}
              d={`M ${CENTER} ${CENTER} L ${point(start)} A ${RADIUS} ${RADIUS} 0 0 1 ${point(end)} Z`} />;
          const labelRadius = denominator === 1 ? 0 : RADIUS * (denominator === 2 ? 0.45 : 0.7);
          x = CENTER + labelRadius * Math.cos(start + angle / 2);
          y = CENTER + labelRadius * Math.sin(start + angle / 2);
        } else {
          const width = SIDE / (bar ? denominator : columns);
          const partHeight = height / (bar ? 1 : rows);
          const left = INSET + (bar ? part : part % columns) * width;
          const top = INSET + (bar ? 0 : Math.floor(part / columns)) * partHeight;
          region = <Rect key={part} {...regionProps} x={left} y={top} width={width} height={partHeight} />;
          x = left + width / 2;
          y = top + partHeight / 2;
        }

        return <React.Fragment key={part}>
          {region}
          <SvgText x={x} y={y} dy="0.35em" textAnchor="middle" pointerEvents="none"
            fill={checked ? COLORS.surface : COLORS.primaryDark} fontFamily={FONTS.extraBold}
            fontSize={denominator > 12 && (bar || rows === 1) ? 8 : 14}>
            {checked ? '✓' : part + 1}
          </SvgText>
        </React.Fragment>;
      })}
      {shape === 'circle'
        ? <Circle cx={CENTER} cy={CENTER} r={RADIUS} fill="none" stroke={COLORS.primaryDark} strokeWidth={2} pointerEvents="none" />
        : <Rect x={INSET} y={INSET} width={SIDE} height={height} fill="none" stroke={COLORS.primaryDark} strokeWidth={2} pointerEvents="none" />}
    </Svg>
  </View>;
}

const styles = StyleSheet.create({
  frame: { width: '100%', maxWidth: 240, aspectRatio: 1, alignSelf: 'center' },
  bar: { aspectRatio: 2.5 },
});
