import { sourceClarification } from '../features/tutoring/sourceClarification';

it('offers a mixed preview without silently changing the original source', () => {
  const source = 'Tính: 4(3)/(5) - 2(1)/(4) = …';
  expect(sourceClarification(source)?.mixedPreview).toBe('Tính: 4 (3)/(5) - 2 (1)/(4) = …');
  expect(sourceClarification('Tính: 2(2)/(3) : 1(2)/(5)')?.mixedPreview).toBe('Tính: 2 (2)/(3) : 1 (2)/(5)');
  expect(source).toBe('Tính: 4(3)/(5) - 2(1)/(4) = …');
});
it('asks for a missing yield unit and rounding place instead of choosing them', () => {
  expect(sourceClarification('Cứ 1 m² thu hoạch được (6)/(5) thóc. Hỏi bao nhiêu tạ thóc?')?.message).toContain('chưa ghi đơn vị');
  expect(sourceClarification('Số thập phân lớn nhất nào được làm tròn đến 90? A. 89,9 B. 89,99 C. 90,1 D. 91,4')?.message).toContain('đến hàng nào');
});
it.each(['Tính: 4 × (3)/(5)', 'Tính: 4 (3)/(5)', 'Làm tròn đến hàng phần mười số 3,14.',
  'Số 35,6 làm tròn đến số tự nhiên gần nhất là:', 'Cứ 1 m² thu hoạch được 6/5 kg thóc. Hỏi bao nhiêu tạ thóc?'])('keeps a clear source usable: %s', source => {
  expect(sourceClarification(source)).toBeNull();
});
