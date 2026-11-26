import { Platform, useWindowDimensions } from 'react-native';

export function isCompactStudentWeb(width: number) {
  return Platform.OS === 'web' && width < 768;
}

export function useIsCompactStudentWeb() {
  return isCompactStudentWeb(useWindowDimensions().width);
}

export function isWideDesktopStudentWeb(width: number) {
  return Platform.OS === 'web' && width >= 1100 && typeof window !== 'undefined'
    && window.matchMedia?.('(hover: hover) and (pointer: fine)').matches === true;
}
