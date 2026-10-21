import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { ProblemSummary } from '../features/tutoring/ProblemSummary';
import type { LessonResponse } from '../features/tutoring/api/TutorService';

let view: TestRenderer.ReactTestRenderer;
const fact = { kind: 'UNDERSTAND' as const, title: 'Dữ kiện', expression: '', answer: 'Lan có 12 bút', unit: '', explanation: 'Đã biết.' };
const question = { ...fact, title: 'Câu hỏi', answer: 'Hỏi Lan có tất cả bao nhiêu bút?' };
const lesson: LessonResponse = { sessionId: 'summary-session-abcdefghijkl', revision: 0, topic: 'Số bút', goal: 'Tìm số bút.',
  understandingSteps: 3, outline: ['Dữ kiện', 'Câu hỏi', 'Đối chiếu', 'Cách làm', 'Tính'], completed: [], stepIndex: 0,
  status: 'READY', feedback: '', step: { kind: 'UNDERSTAND', title: 'Dữ kiện', explanation: 'Đọc đề.', question: 'Điều gì đã biết?',
    choices: ['Lan có 12 bút', question.answer], expression: '', unit: '', workExcerpt: '' } };
const text = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
const render = (value = lesson) => act(() => { view = TestRenderer.create(<ProblemSummary lesson={value} />); });
const toggle = () => view.root.findAll(node => node.props.accessibilityLabel === 'Xem lại tóm tắt đề' && node.props.onPress)[0];
afterEach(() => { if (view) act(() => view.unmount()); });

it('guides how to summarize without preclassifying unanswered source choices', () => {
  render({ ...lesson, summary: { givens: ['Private premature fact'], question: 'Private premature question?' } });
  expect(text()).toContain('Tìm các số, đơn vị và mối liên hệ');
  expect(text()).toContain('Đã biết'); expect(text()).toContain('Cần tìm');
  expect(text()).not.toContain('Private premature');
  expect(text()).not.toContain('Bản tóm tắt từ đề');
});

it('labels an individually checked fact as partial instead of a complete summary', () => {
  render({ ...lesson, stepIndex: 1, completed: [fact] });
  expect(text()).toContain('Dữ kiện em vừa chọn');
  expect(text()).toContain('Đây là một dữ kiện');
  expect(text()).toContain('Lan có 12 bút');
  expect(text()).not.toContain('Bản tóm tắt từ đề');
});

it('groups the source givens including qualitative relationships after both choices', () => {
  render({ ...lesson, stepIndex: 2, completed: [fact, question], summary: {
    givens: ['Lan có 12 bút', 'được thêm 5 bút', 'không cho đi chiếc nào'], question: question.answer,
  } });
  expect(text()).toContain('Bản tóm tắt từ đề');
  expect(text()).toContain('không cho đi chiếc nào');
  expect(text()).toContain(question.answer);
  expect(text()).not.toContain('17');
});

it('keeps summary available for review without crowding the calculation step', () => {
  render({ ...lesson, stepIndex: 3, completed: [fact, question, { ...fact, answer: 'Đúng' }],
    step: { ...lesson.step!, kind: 'MATH' }, summary: { givens: [fact.answer], question: question.answer } });
  expect(toggle().props['aria-expanded']).toBe(false);
  expect(text()).not.toContain(fact.answer);
  act(() => toggle().props.onPress());
  expect(toggle().props['aria-expanded']).toBe(true);
  expect(text()).toContain('Bản tóm tắt từ đề');
  act(() => toggle().props.onPress());
  expect(text()).not.toContain(fact.answer);
});

it('does not claim structured reading support for legacy or unsupported sources', () => {
  render({ ...lesson, understandingSteps: 0 });
  expect(text()).toBe('');
});
