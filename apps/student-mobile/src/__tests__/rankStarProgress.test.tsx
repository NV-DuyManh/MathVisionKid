import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { RankStarProgress } from '../features/student-profile/RankGuide';

it.each([
  [0, 3, 0], [1, 3, 1], [3, 3, 3], [2, 4, 2], [4, 5, 4], [5, 5, 5],
  [-1, 3, 0], [8, 5, 5],
])('shows %i earned out of %i stars with %i filled slots', (earned, goal, filled) => {
  let tree!: TestRenderer.ReactTestRenderer;
  act(() => { tree = TestRenderer.create(<RankStarProgress earned={earned} goal={goal} />); });
  const all = tree.root.findAll(node => node.type === 'View' && node.props.testID === 'rank-star-filled');
  const empty = tree.root.findAll(node => node.type === 'View' && node.props.testID === 'rank-star-empty');
  expect(all).toHaveLength(filled);
  expect(empty).toHaveLength(goal - filled);
  expect(JSON.stringify(tree.toJSON())).toContain(filled + '/' + goal);
  act(() => tree.unmount());
});

it('uses a compact progress bar for the 35 and 40 star tiers', () => {
  let tree!: TestRenderer.ReactTestRenderer;
  act(() => { tree = TestRenderer.create(<RankStarProgress earned={12} goal={35} />); });
  expect(JSON.stringify(tree.toJSON())).toContain('12/35');
  expect(tree.root.findAll(node => node.props.testID === 'rank-star-filled')).toHaveLength(0);
  act(() => { tree.update(<RankStarProgress earned={40} goal={40} />); });
  expect(JSON.stringify(tree.toJSON())).toContain('40/40');
  act(() => tree.unmount());
});

it('omits the indicator for top ranks and avoids claiming a progress value without a profile', () => {
  let tree!: TestRenderer.ReactTestRenderer;
  act(() => { tree = TestRenderer.create(<RankStarProgress earned={0} goal={0} />); });
  expect(tree.toJSON()).toBeNull();
  act(() => { tree.update(<RankStarProgress goal={3} />); });
  expect(JSON.stringify(tree.toJSON())).not.toContain('0/3');
  act(() => tree.unmount());
});
