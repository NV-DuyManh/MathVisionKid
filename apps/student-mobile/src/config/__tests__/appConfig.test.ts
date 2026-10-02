import { getAppBranding, getFeatureFlags } from '../appConfig';
import { COLORS, MATHVISION_COLORS, getThemeColors } from '../../constants/theme';

describe('One MathVision configuration', () => {
  const original = process.env.EXPO_PUBLIC_APP_MODE;
  afterEach(() => { process.env.EXPO_PUBLIC_APP_MODE = original; });
  test.each([undefined, 'OBSOLETE_STANDALONE_MODE', 'MATHVISION_KIDS'])('keeps both recognition domains and privacy for obsolete setting %s', value => {
    process.env.EXPO_PUBLIC_APP_MODE = value;
    expect(getAppBranding().name).toBe('MathVision Kids');
    const flags = getFeatureFlags();
    expect(flags.showArithmeticMode).toBe(true);
    expect(flags.showMathCalculations).toBe(true);
    expect(flags.showHandwritingPipeline).toBe(true);
    expect(flags.showPrivacyProtection).toBe(true);
    expect(flags).not.toHaveProperty('bypassLogin');
    expect(flags).not.toHaveProperty('bypassPrivacyMasking');
    expect(getThemeColors()).toBe(MATHVISION_COLORS);
    expect(COLORS.aiSuggestionBg).toBeDefined();
  });
});
