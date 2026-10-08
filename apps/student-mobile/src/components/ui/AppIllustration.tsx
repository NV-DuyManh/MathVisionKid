import React from 'react';
import { Image, ImageProps, ImageRef } from 'expo-image';

const SOURCES = [
  require('../../../assets/illustrations/student-avatar.png'),
  require('../../../assets/illustrations/mathvision-star.png'),
  require('../../../assets/illustrations/saved-folder.png'),
  require('../../../assets/illustrations/practice-notebook.png'),
  require('../../../assets/illustrations/progress-bars.png'),
  require('../../../assets/illustrations/encouragement-crown.png'),
  require('../../../assets/illustrations/streak-flame.png'),
  require('../../../assets/illustrations/reward-star.png'),
  require('../../../assets/images/mathvision-icon-v2.png'),
];
const ready = new Map<number, ImageRef>();
let pending: Promise<void> | null = null;

export function prepareIllustrations(): Promise<void> {
  if (!pending) {
    const loading = Promise.all(SOURCES.map(async source => {
      if (!ready.has(source)) ready.set(source, await Image.loadAsync(source, { maxWidth: 640, maxHeight: 640 }));
    }));
    let timeout: ReturnType<typeof setTimeout>;
    pending = Promise.race([loading, new Promise<never>((_, reject) => {
      timeout = setTimeout(() => reject(new Error('Illustration load timed out')), 15000);
    })]).then(() => {}).finally(() => { clearTimeout(timeout); pending = null; });
  }
  return pending;
}

export function AppIllustration({ source, resizeMode, contentFit, ...props }: Omit<ImageProps, 'source'> & { source: number }) {
  return <Image {...props} source={ready.get(source) || source} contentFit={contentFit || (resizeMode === 'cover' ? 'cover' : 'contain')} transition={0} />;
}
