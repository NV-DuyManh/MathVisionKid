import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';

const root = path.resolve(__dirname, '..');
const mascotScreens = [
  'features/onboarding/WelcomeScreen.tsx', 'app/(tabs)/lessons.tsx', 'app/(tabs)/_layout.tsx', 'app/learning/math-guide.tsx',
  'app/quiz/index.tsx', 'components/home/HomeDashboard.tsx', 'components/ui/AppIllustration.tsx',
  'components/ui/BrandLockup.tsx', 'components/ui/StudentResultShell.tsx', 'features/quiz/QuizInvitation.tsx',
  'features/tutoring/LessonQuestion.tsx', 'features/recognition/components/RecognitionProgress.tsx',
];

it('ships the owner-provided robot and configures startup icons from it', () => {
  const mobile = path.resolve(root, '..');
  const mascot = fs.readFileSync(path.join(mobile, 'assets/illustrations/robot-mascot.png'));
  expect(createHash('sha256').update(mascot).digest('hex')).toBe('5d7f2e3e3b3dbaf23c2fdca1d0b84be3d6a1ab75984ade60ebc584b5cd974bfa');
  const config = JSON.parse(fs.readFileSync(path.join(mobile, 'app.json'), 'utf8')).expo;
  expect(config.icon).toBe('./assets/images/mathvision-robot-icon.png');
  expect(config.ios.icon).toBe(config.icon);
  expect(config.web.favicon).toBe(config.icon);
  expect(config.android.adaptiveIcon.foregroundImage).toBe('./assets/images/mathvision-robot-adaptive.png');
  expect(config.plugins.find((plugin: string | [string, object]) => Array.isArray(plugin) && plugin[0] === 'expo-splash-screen')[1].image).toBe(config.icon);
});

it('uses the approved robot throughout active student mascot surfaces', () => {
  for (const file of mascotScreens) {
    const source = fs.readFileSync(path.join(root, file), 'utf8');
    expect(source).toContain('robot-mascot');
    expect(source).not.toMatch(/assets\/illustrations\/(?:web\/)?mathvision-star\.(?:png|webp)/);
    expect(source).not.toContain('star-listening.png');
    expect(source).not.toMatch(/(?:Sao [Nn]hỏ|SAO NHỎ|CÙNG SAO|Cùng Sao|cùng Sao|Sao đang)/);
  }
});

it('keeps the selectable star avatar and completed-day stars independent of the mascot', () => {
  const profile = fs.readFileSync(path.join(root, 'features/student-profile/ProfileCards.tsx'), 'utf8');
  const home = fs.readFileSync(path.join(root, 'components/home/HomeDashboard.tsx'), 'utf8');
  expect(profile).toContain("id: 'star'");
  expect(home).toContain('reward-star.png');
});
