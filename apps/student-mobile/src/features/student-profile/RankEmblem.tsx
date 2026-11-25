import React, { useId } from 'react';
import Svg, { Defs, LinearGradient, Stop, Path } from 'react-native-svg';
import { ApprovedEmblem } from './ApprovedEmblem';
import { approvedRankAsset } from './ApprovedRankAssets';

export function RankEmblem({ name, size = 76 }: { name: string; size?: number }) {
  const id = useId().replace(/[^\w-]/g, '');
  if (name.replace(/ [IV]+$/, '') !== 'Sắt') return <ApprovedEmblem source={approvedRankAsset(name)} size={size} />;
  return <Svg width={size} height={size} viewBox="-3 -3 102 102" accessible={false} aria-hidden>
    <Defs>
      <LinearGradient id={id+'steel'} x1="0%" y1="0%" x2="100%" y2="100%">
        <Stop offset="0" stopColor="#EDF8FF"/><Stop offset={0.35} stopColor="#8DB0C7"/><Stop offset={0.62} stopColor="#D4E9F2"/><Stop offset="1" stopColor="#47637C"/>
      </LinearGradient>
      <LinearGradient id={id+'core'} x1="0%" y1="0%" x2="0%" y2="100%">
        <Stop offset="0" stopColor="#6E92AD"/><Stop offset="1" stopColor="#28435F"/>
      </LinearGradient>
    </Defs>
    <Path d="M48 9 82 28 77 59 66 75 48 88 30 75 19 59 14 28Z" fill={'url(#'+id+'steel)'} stroke="#38566F" strokeWidth="2" strokeLinejoin="round"/>
    <Path d="M48 18 73 32 69 57 59 70 48 79 37 70 27 57 23 32Z" fill={'url(#'+id+'core)'} stroke="#DFEFF7" strokeWidth="2"/>
    <Path d="M48 28 55 43 72 45 60 57 63 73 48 65 33 73 36 57 24 45 41 43Z" fill="#91C8DD" stroke="#DDF5FF" strokeWidth="1.5" strokeLinejoin="round"/>
    <Path d="M48 28 48 50 41 43Z M48 50 60 57 63 73Z" fill="#E7F7FF" opacity=".8"/>
  </Svg>;
}
