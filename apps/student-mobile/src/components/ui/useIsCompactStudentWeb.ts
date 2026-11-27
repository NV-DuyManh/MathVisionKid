import { Platform, useWindowDimensions } from 'react-native';
import { STUDENT_WEB } from '../../constants/studentWebDesign';

export function isCompactStudentWeb(width: number) {
  return Platform.OS === 'web' && width < STUDENT_WEB.workspaceBreakpoint;
}

export function useIsCompactStudentWeb() {
  return isCompactStudentWeb(useWindowDimensions().width);
}

export function isDesktopStudentWeb(width: number) {
  return Platform.OS === 'web' && !isCompactStudentWeb(width) && typeof window !== 'undefined'
    && window.matchMedia?.('(hover: hover) and (pointer: fine)').matches === true;
}

export function isWideDesktopStudentWeb(width: number) {
  return width >= 1100 && isDesktopStudentWeb(width);
}
