import { Platform, useWindowDimensions } from 'react-native';

export function isCompactStudentWeb(width: number) {
  return Platform.OS === 'web' && width < 768;
}

export function useIsCompactStudentWeb() {
  return isCompactStudentWeb(useWindowDimensions().width);
}
