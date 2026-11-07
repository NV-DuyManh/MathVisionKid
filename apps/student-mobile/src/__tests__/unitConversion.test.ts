import { convertUnits, UNIT_GROUPS, type UnitGroup } from '../features/calculator/convertUnits';

it.each([
  ['length', '15,25', 'm', 'cm', '1525 cm'], ['length', '219', 'mm', 'm', '0,219 m'],
  ['area', '1,7', 'km²', 'ha', '170 ha'], ['area', '219000', 'm²', 'ha', '21,9 ha'],
  ['area', '382', 'mm²', 'dm²', '0,0382 dm²'], ['area', '1', 'ha', 'hm²', '1 hm²'],
  ['mass', '1', 'tấn', 'kg', '1000 kg'], ['mass', '5,04', 'tấn', 'kg', '5040 kg'],
  ['mass', '5', 'tạ', 'kg', '500 kg'], ['mass', '1', 'yến', 'g', '10000 g'],
  ['volume', '7500', 'ml', 'l', '7,5 l'], ['volume', '1', 'm³', 'l', '1000 l'],
  ['volume', '1', 'l', 'cm³', '1000 cm³'], ['volume', '1', 'ml', 'dm³', '0,001 dm³'],
  ['length', '2 1/4', 'm', 'cm', '225 cm'], ['length', '1/3', 'm', 'cm', '100/3 cm'],
  ['area', '999999,9999', 'km²', 'mm²', '999999999900000000 mm²'],
  ['length', '0', 'm', 'cm', '0 cm'],
] as const)('converts %s %s %s to %s exactly', (group, value, unit, target, expected) => {
  expect(convertUnits(group, [{ value, unit }], target).result).toBe(expected);
});

it.each([
  ['length', '15', 'm', '25', 'cm', 'm', '15,25 m'],
  ['mass', '2', 'tấn', '35', 'kg', 'kg', '2035 kg'],
  ['mass', '5', 'tạ', '7', 'kg', 'tấn', '0,507 tấn'],
  ['area', '5', 'm²', '6', 'dm²', 'm²', '5,06 m²'],
  ['area', '36', 'km²', '50', 'ha', 'km²', '36,5 km²'],
  ['volume', '15', 'l', '78', 'ml', 'l', '15,078 l'],
  ['length', '1/3', 'm', '2/3', 'm', 'm', '1 m'],
] as const)('adds two compatible %s measurements', (group, value, unit, next, nextUnit, target, expected) => {
  const answer = convertUnits(group, [{ value, unit }, { value: next, unit: nextUnit }], target);
  expect(answer.result).toBe(expected);
  expect(answer.steps.join(' ')).toContain('Cộng hai số đo');
});

it('uses squared and cubed scale factors and explains mixed numbers without rounding', () => {
  expect(convertUnits('area', [{ value: '2', unit: 'm²' }], 'dm²').steps.join(' ')).toContain('× 100');
  expect(convertUnits('volume', [{ value: '2', unit: 'm³' }], 'dm³').steps.join(' ')).toContain('× 1000');
  expect(convertUnits('length', [{ value: '2 1/4', unit: 'm' }], 'km').steps.join(' ')).toContain('Đổi hỗn số');
});

it.each(['', '-1', '2+3', '1e3', 'NaN', '1/0', '2 4/3', '1000000', '1,00001'])('rejects invalid measurement %s without inventing a result', value => {
  expect(() => convertUnits('length', [{ value, unit: 'm' }], 'cm')).toThrow();
});
it('rejects mismatched dimensions and missing quantities', () => {
  expect(() => convertUnits('length', [{ value: '1', unit: 'm' }], 'kg')).toThrow();
  expect(() => convertUnits('length', [{ value: '1', unit: 'm²' }], 'cm')).toThrow();
  expect(() => convertUnits('length', [], 'cm')).toThrow();
});

it('round-trips all supported unit pairs without losing their exact scale', () => {
  for (const group of Object.keys(UNIT_GROUPS) as UnitGroup[]) {
    for (const [from] of UNIT_GROUPS[group].units) for (const [to] of UNIT_GROUPS[group].units) {
      const converted = convertUnits(group, [{ value: '1', unit: from }], to).result;
      // Independent check of the physical ratio, not the formatting algorithm.
      const numeric = Number(converted.slice(0, -to.length).trim().replace(',', '.'));
      const fromScale = UNIT_GROUPS[group].units.find(([unit]) => unit === from)![1];
      const toScale = UNIT_GROUPS[group].units.find(([unit]) => unit === to)![1];
      expect(numeric).toBeCloseTo(fromScale / toScale, 12);
    }
  }
});
