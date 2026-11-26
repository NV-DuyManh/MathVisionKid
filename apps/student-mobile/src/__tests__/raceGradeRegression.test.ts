import path from 'node:path';

const source = path.join(path.dirname(require.resolve('@mathvisionkid/training-games')), '..');
const { QuestionGenerator, validateRaceQuestion, raceFingerprint } = require(path.join(source, 'games/race-to-finish/logic/questions'));
const { EnergyQuestions, gradeFamilies } = require(path.join(source, 'games/energy-defense/logic/questions'));
const { defaultSetupName } = require(path.join(source, 'games/race-to-finish/logic/playerIdentity'));
const { QuestionHistory } = require(path.join(source, 'shared/math/questionHistory'));
const { PRNG } = require(path.join(source, 'shared/math/prng'));
const history = () => new QuestionHistory({ getItem: async () => null, setItem: async () => {} }, 'regression');

test('grade 5 race remains varied and never falls back to early-primary natural arithmetic', () => {
  const random = new PRNG(20261125);
  const generator = new QuestionGenerator(() => random.next(), history(), 5);
  const identities = new Set();
  for (let i = 0; i < 400; i++) {
    const question = generator.next('tile_0');
    expect(validateRaceQuestion(question)).toBe(true);
    expect(question.category).not.toMatch(/^natural-/);
    identities.add(raceFingerprint(question));
  }
  expect(identities.size).toBe(400);
  const constant = new QuestionGenerator(() => 0, history(), 5);
  for (let i = 0; i < 100; i++) expect(constant.next('tile_0').category).not.toMatch(/^natural-/);
});

test('grade 1 still gets natural arithmetic and grade 5 defense starts with decimals', () => {
  const race = new QuestionGenerator(() => .4, history(), 1);
  for (let i = 0; i < 30; i++) {
    const question = race.next('tile_0');
    expect(question.prompt).toMatch(/^Tính: \d+ [−+] \d+$/);
    expect(question.answer.d).toBe(1);
  }
  expect(gradeFamilies(5, 'warmup')).not.toContain('natural');
  const random = new PRNG(51), defense = new EnergyQuestions(() => random.next(), history(), 5);
  for (let i = 0; i < 50; i++) {
    const question = defense.next('warmup', i);
    expect(question.explanation).toContain(',');
    expect(question.validCombosCount).toBe(1);
  }
});

test('automatic participant names follow the selected character without a machine suffix', () => {
  expect(defaultSetupName('single', 1, 'penguin')).toBe('Cánh Cụt');
  expect(defaultSetupName('single', 1, 'fox')).toBe('Cáo Con');
  expect(defaultSetupName('single', 0, 'fox')).toBe('Em');
});
