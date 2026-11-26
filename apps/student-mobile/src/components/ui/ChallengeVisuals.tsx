import React from 'react';
import { Platform, View } from 'react-native';
import Svg, { Circle, Ellipse, Path } from 'react-native-svg';
import { AppButton } from './AppButton';
import { MATHVISION_COLORS } from '../../constants/theme';

export const CHALLENGE_COLORS = {
  ...MATHVISION_COLORS,
  deepPurple: '#39209B',
  yellow: '#FFD75E',
  lavender: '#EEE9FF',
  ink: '#18164C',
  line: '#E3DFF0',
  green: '#16735B',
  warm: '#FFF8E3',
};

// SPA web exports do not render Expo Router's static +html document.
export function ChallengeWebStyles() {
  if (Platform.OS !== 'web') return null;
  return <style>{`
    [data-challenge="true"] :is([role], input, textarea):focus-visible { outline: 3px solid #7055F6; outline-offset: 3px; }
    @media (hover: hover) and (pointer: fine) {
      [data-challenge="true"] [role="button"]:hover:not([aria-disabled="true"]) { box-shadow: 0 0 0 2px #7055F6; }
      [data-challenge="true"] [role="radio"]:hover:not([aria-disabled="true"]) { border-color: #7055F6; }
    }
  `}</style>;
}

/** Decorative vector artwork; earned rewards are always labelled by the caller. */
export function StarMedal({ size = 120 }: { size?: number }) {
  return <View accessible={false} style={{ width: size, height: size }}>
    <Svg width="100%" height="100%" viewBox="0 0 160 160" accessible={false}>
      <Ellipse cx="80" cy="140" rx="44" ry="7" fill="#18164C" opacity=".09" />
      <Circle cx="80" cy="76" r="61" fill="#EEE9FF" />
      <Circle cx="80" cy="76" r="50" fill="none" stroke="#BEB0F6" strokeWidth="1.5" strokeDasharray="4 7" />
      <Path d="M80 25 96 57 132 62 106 88 112 124 80 107 48 124 54 88 28 62 64 57Z" fill="#D99620" stroke="#18164C" strokeWidth="2" strokeLinejoin="round" />
      <Path d="M80 20 96 52 132 57 106 83 112 119 80 102 48 119 54 83 28 57 64 52Z" fill="#FFD75E" stroke="#18164C" strokeWidth="2" strokeLinejoin="round" />
      <Path d="m80 20 0 46-26 17 10-31Z" fill="#FFF0AC" />
      <Path d="m96 52-16 14 26 17 26-26Z" fill="#FFE89A" />
      <Path d="m22 28 0 12m-6-6h12m109 70v12m-6-6h12" stroke="#7055F6" strokeWidth="3" strokeLinecap="round" />
      <Circle cx="135" cy="34" r="4" fill="#FFD75E" />
    </Svg>
  </View>;
}

export function ChallengeButton(props: React.ComponentProps<typeof AppButton>) {
  const primary = !props.variant || props.variant === 'primary';
  return <AppButton {...props} style={{ minHeight: 54, borderRadius: 16, borderBottomWidth: primary ? 3 : 0, borderBottomColor: CHALLENGE_COLORS.deepPurple,
      backgroundColor: props.disabled && !props.loading ? CHALLENGE_COLORS.border : primary ? CHALLENGE_COLORS.primary : props.variant === 'ghost' ? 'transparent' : CHALLENGE_COLORS.lavender,
      ...props.style,
  }} textStyle={{ color: props.disabled && !props.loading ? CHALLENGE_COLORS.textMuted : primary ? '#FFFFFF' : CHALLENGE_COLORS.deepPurple, ...props.textStyle }} />;
}
