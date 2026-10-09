import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { Image } from 'expo-image';
import { AppIllustration, prepareIllustrations } from '../components/ui/AppIllustration';

jest.mock('expo-image', () => ({ Image: Object.assign((props: any) => require('react').createElement('PreparedImage', props), { loadAsync: jest.fn() }) }));

it('loads the critical art concurrently, retries failed downloads, and reuses decoded references', async () => {
  (Image.loadAsync as jest.Mock).mockRejectedValue(new Error('offline'));
  await expect(prepareIllustrations()).rejects.toThrow('offline');
  (Image.loadAsync as jest.Mock).mockClear();
  const done: (() => void)[] = [];
  let count = 0;
  (Image.loadAsync as jest.Mock).mockImplementation(source => new Promise(resolve => {
    if (count++ === 0) throw new Error('one image failed quickly');
    done.push(() => resolve({ nativeRef: source }));
  }));
  await expect(prepareIllustrations()).rejects.toThrow('one image failed quickly');
  expect(Image.loadAsync).toHaveBeenCalledTimes(9);
  const first = prepareIllustrations();
  expect(Image.loadAsync).toHaveBeenCalledTimes(10);
  expect(prepareIllustrations()).toBe(first);
  const source = (Image.loadAsync as jest.Mock).mock.calls[0][0];
  expect((Image.loadAsync as jest.Mock).mock.calls[0][1]).toEqual({ maxWidth: 640, maxHeight: 640 });
  done.forEach(resolve => resolve());
  await first;
  await prepareIllustrations();
  expect(Image.loadAsync).toHaveBeenCalledTimes(10);
  let view: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<AppIllustration source={source} />); });
  expect(view!.root.findByType('PreparedImage' as any).props.source).toEqual({ nativeRef: source });
  expect(view!.root.findByType('PreparedImage' as any).props.transition).toBe(0);
  act(() => view!.unmount());
});
