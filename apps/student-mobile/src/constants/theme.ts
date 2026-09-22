import { isHandAIMode, AppMode } from '../config/appMode';

export const MATHVISION_COLORS = {
  primary: '#2563EB',
  primaryDark: '#1D4ED8',
  primaryLight: '#DBEAFE',
  secondary: '#F59E0B',
  secondaryDark: '#D97706',
  secondaryLight: '#FEF3C7',
  accent: '#10B981',
  background: '#F8FAFC',
  surface: '#FFFFFF',
  surfaceSubdued: '#EFF6FF',
  textPrimary: '#0F172A',
  textSecondary: '#475569',
  textMuted: '#64748B',
  success: '#16A34A',
  successLight: '#DCFCE7',
  warning: '#D97706',
  warningLight: '#FEF3C7',
  error: '#DC2626',
  errorLight: '#FEE2E2',
  errorText: '#B91C1C',
  review: '#7C3AED',
  reviewLight: '#EDE9FE',
  border: '#E2E8F0',
  borderFocus: '#2563EB',
  pastelBlue: '#EFF6FF',
  pastelGreen: '#F0FDF4',
  pastelPeach: '#FFF7ED',
  pastelPurple: '#FAF5FF',
  pastelAmber: '#FEFCE8',
};

export const HAND_AI_COLORS = {
  primary: '#4F46E5', // Tech Indigo AI
  primaryDark: '#3730A3',
  primaryLight: '#EEF2FF',
  secondary: '#0891B2', // Cyan
  secondaryDark: '#0E7490',
  secondaryLight: '#E0F2FE',
  accent: '#10B981', // Emerald
  background: '#F8FAFC',
  surface: '#FFFFFF',
  surfaceSubdued: '#F5F3FF',
  textPrimary: '#0F172A',
  textSecondary: '#475569',
  textMuted: '#64748B',
  success: '#16A34A',
  successLight: '#DCFCE7',
  warning: '#D97706',
  warningLight: '#FEF3C7',
  error: '#DC2626',
  errorLight: '#FEE2E2',
  errorText: '#B91C1C',
  review: '#7C3AED',
  reviewLight: '#EDE9FE',
  border: '#E2E8F0',
  borderFocus: '#4F46E5',
  pastelBlue: '#EEF2FF',
  pastelGreen: '#F0FDF4',
  pastelPeach: '#FFF7ED',
  pastelPurple: '#FAF5FF',
  pastelAmber: '#FEFCE8',
};

export function getThemeColors(mode?: AppMode) {
  if (mode === 'HAND_AI' || (!mode && isHandAIMode())) {
    return HAND_AI_COLORS;
  }
  return MATHVISION_COLORS;
}

export const COLORS: typeof MATHVISION_COLORS = new Proxy(MATHVISION_COLORS, {
  get(target, prop: string) {
    const active = isHandAIMode() ? HAND_AI_COLORS : MATHVISION_COLORS;
    return (active as any)[prop] ?? (target as any)[prop];
  },
});


export const SIZES = {
  xs: 4,
  base: 8,
  small: 12,
  medium: 16,
  large: 20,
  xlarge: 24,
  xxlarge: 32,
  hero: 48,
  minTouchTarget: 48,
  radiusSm: 8,
  radiusMd: 14,
  radiusLg: 20,
  radiusXl: 24,
  cardRadius: 20,
  buttonRadius: 26,
  inputRadius: 14,
  pillRadius: 999,
};

export const SHADOWS = {
  small: {
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  medium: {
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 4,
  },
  large: {
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 8,
  },
};
