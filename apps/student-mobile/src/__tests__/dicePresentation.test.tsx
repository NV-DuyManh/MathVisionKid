import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { Circle, G } from 'react-native-svg';
import path from 'node:path';

// Exercise the installed artifact produced by the canonical game builder.
const { DiceModel } = require(path.join(path.dirname(require.resolve('@mathvisionkid/training-games')), '../games/race-to-finish/components/DiceModel'));

test.each([1, 2, 3, 4, 5, 6])('the main face renders exactly %i recessed pips', value => {
  let view: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<DiceModel value={value} />); });
  const face = view!.root.findAllByType(G).find(node => node.props.testID === `dice-front-${value}`)!;
  expect(face).toBeDefined();
  expect(face.findAllByType(Circle).filter(node => node.props.testID === 'dice-front-pip')).toHaveLength(value);
  act(() => view!.unmount());
});
