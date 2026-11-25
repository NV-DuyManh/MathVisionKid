import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { ProfileRankCard } from '../features/student-profile/ProfileCards';
import { ApprovedEmblem } from '../features/student-profile/ApprovedEmblem';
import { RankEmblem } from '../features/student-profile/RankEmblem';
import type { StudentProfile } from '../features/student-profile/profileApi';

const profile: StudentProfile = {
  displayName: 'Bạn nhỏ', gradeLevel: 5, joinedAt: null, classrooms: [], avatar: 'star',
  leaderboardVisible: true, publicAlias: 'Hươu Sao', selectedTitle: 'luyen-khi', stars: 1,
  rank: { name: 'Sắt III', masterStars: 0, progress: 1, goal: 3 }, highestRank: 'Sắt III', position: 1,
  stats: { lessons: 3, quizzes: 0, games: 0, days: 1, week: 3, month: 3, today: 3, streak: 1 },
  titles: [{ id: 'luyen-khi', name: 'Luyện Khí', rarity: 'Phổ biến', description: 'Hoàn thành 3 bài học', progress: 3, goal: 3, unlocked: true }],
  history: [],
};

it('does not mix an equipped cultivation title into the star rank card', () => {
  let tree!: TestRenderer.ReactTestRenderer;
  act(() => { tree = TestRenderer.create(<ProfileRankCard profile={profile} />); });
  expect(tree.root.findByType(RankEmblem).props.name).toBe('Sắt III');
  expect(JSON.stringify(tree.toJSON())).not.toContain('Luyện Khí');
  act(() => tree.unmount());
});

it('renders all 26 rank divisions with shared major rank art', () => {
  let tree!: TestRenderer.ReactTestRenderer;
  const ranks = ['Sắt III', 'Sắt II', 'Sắt I', 'Đồng III', 'Đồng II', 'Đồng I', 'Bạc III', 'Bạc II', 'Bạc I', 'Vàng III', 'Vàng II', 'Vàng I', 'Bạch Kim V', 'Bạch Kim IV', 'Bạch Kim III', 'Bạch Kim II', 'Bạch Kim I', 'Kim Cương V', 'Kim Cương IV', 'Kim Cương III', 'Kim Cương II', 'Kim Cương I', 'Cao Thủ', 'Đại Cao Thủ', 'Thách Đấu', 'Huyền Thoại'];
  act(() => { tree = TestRenderer.create(<>{ranks.map(name => <RankEmblem key={name} name={name} size={22} />)}</>); });
  expect(tree.root.findAllByType(RankEmblem)).toHaveLength(26);
  const icons = tree.root.findAllByType(ApprovedEmblem);
  expect(icons).toHaveLength(23);
  expect(icons.every(icon => icon.props.source !== undefined && icon.props.size === 22)).toBe(true);
  expect(icons.slice(0,3).every(icon => icon.props.source === icons[0].props.source)).toBe(true);
  act(() => tree.unmount());
});
