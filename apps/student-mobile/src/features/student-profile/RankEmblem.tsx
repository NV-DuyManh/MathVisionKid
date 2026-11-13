import React, { useId } from 'react';
import { Image, View } from 'react-native';
import Svg, { Defs, LinearGradient, Path, Stop } from 'react-native-svg';

const metals = {
  'Đồng': require('../../../assets/ranks/bronze.png'),
  'Bạc': require('../../../assets/ranks/silver.png'),
  'Vàng': require('../../../assets/ranks/gold.png'),
  'Bạch Kim': require('../../../assets/ranks/platinum.png'),
  'Kim Cương': require('../../../assets/ranks/diamond.png'),
} as const;

const crests = {
  'Tinh Anh': ['#F3BDFF', '#642494', '#D480FF', 'M9 28 25 34 48 7 71 34 87 28 77 53 62 58 48 88 34 58 19 53Z'],
  'Cao Thủ': ['#FFE3A0', '#963D13', '#FFAA3A', 'M5 21 27 32 38 14 48 3 58 14 69 32 91 21 82 47 68 58 63 73 48 90 33 73 28 58 14 47Z'],
  'Đại Cao Thủ': ['#FFF2AB', '#953A21', '#FB6750', 'M1 17 22 26 34 12 48 3 62 12 74 26 95 17 84 50 70 57 77 68 62 71 48 94 34 71 19 68 26 57 12 50Z'],
  'Chiến Tướng': ['#FFDEB1', '#902A43', '#FA668B', 'M3 18 25 31 32 9 48 18 64 9 71 31 93 18 88 44 74 53 75 66 64 65 48 92 32 65 21 66 22 53 8 44Z'],
  'Chiến Thần': ['#CAFCFF', '#214C9A', '#66DFFF', 'M3 25 21 35 28 13 41 19 48 2 55 19 68 13 75 35 93 25 82 52 68 59 67 74 48 94 29 74 28 59 14 52Z'],
  'Thách Đấu': ['#FFF2A6', '#A45325', '#7AF2FF', 'M1 21 21 30 28 12 40 18 48 2 56 18 68 12 75 30 95 21 88 46 76 53 80 62 66 65 60 83 48 95 36 83 30 65 16 62 20 53 8 46Z'],
} as const;

export function RankEmblem({ name, size = 76 }: { name: string; size?: number }) {
  const id = useId().replace(/[^\w-]/g, '');
  const tier = name.replace(/ [IV]+$/, '');
  const source = metals[tier as keyof typeof metals];
  const [light, dark, gem, crest] = crests[tier as keyof typeof crests] ?? crests['Tinh Anh'];
  return <View accessible={false} aria-hidden style={{ width: size, height: size, flexShrink: 0 }}>
    {source ? <Image source={source} style={{ width: size, height: size }} resizeMode="contain" /> :
      <Svg width={size} height={size} viewBox="0 0 96 96">
        <Defs><LinearGradient id={id} x1="0%" y1="0%" x2="0%" y2="100%">
          <Stop offset="0" stopColor={light} /><Stop offset="1" stopColor={dark} />
        </LinearGradient></Defs>
        <Path d={crest} fill={`url(#${id})`} stroke={light} strokeWidth="2.5" strokeLinejoin="round" />
        <Path d="M16 34 35 43 48 19 61 43 80 34 69 51 61 54 48 80 35 54 27 51Z" fill={dark} stroke={light} strokeWidth="1.5" />
        <Path d="M48 28 64 48 48 70 32 48Z" fill={gem} stroke={light} strokeWidth="2" />
        <Path d="M48 30 53 48 48 68 43 48Z" fill="#FFF" opacity=".8" />
      </Svg>}
  </View>;
}
