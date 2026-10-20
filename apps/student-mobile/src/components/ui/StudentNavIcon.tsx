import React from 'react';
import { Image } from 'expo-image';

const icons = {
  index: require('../../../assets/icons/student-home.svg'),
  lessons: require('../../../assets/icons/student-lessons.svg'),
  achievements: require('../../../assets/icons/student-achievements.svg'),
  profile: require('../../../assets/icons/student-profile.svg'),
};

export function StudentNavIcon({ name, size = 32 }: { name: keyof typeof icons; size?: number }) {
  return <Image source={icons[name]} style={{ width: size, height: size }} contentFit="contain" accessible={false} alt="" transition={0} />;
}
