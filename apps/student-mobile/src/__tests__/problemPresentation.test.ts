import { problemPresentation } from '../components/domain/problemPresentation';

it('puts each original answer on its own line without changing values', () => {
  const source = 'Câu 6. Tính 17/25 + 32/15: A. 49/40 B. 211/75 C. 211/40 D. 49/75';
  expect(problemPresentation(source)).toBe('Câu 6. Tính 17/25 + 32/15:\nA. 49/40\nB. 211/75\nC. 211/40\nD. 49/75');
  expect(problemPresentation(problemPresentation(source))).toBe(problemPresentation(source));
});

it.each(['Cho hình thang ABCD có AB = 8 cm.', 'a. 15 dm 2 cm = ... dm b. 9 tấn 4 kg = ... tấn',
  'Chọn A. hoặc B. trước khi làm.', 'A. 1 C. 2 B. 3 D. 4'])('keeps incomplete groups and geometry intact: %s', source => {
  expect(problemPresentation(source)).toBe(source);
});
