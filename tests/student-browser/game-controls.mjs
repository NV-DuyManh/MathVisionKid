import { expect } from '@playwright/test';

export async function chooseTrainingGrade(page,game,grade=5) {
  if(!['race-to-finish','terrain-racing','energy-defense'].includes(game))return;
  await expect(page.getByTestId(`grade-selection-${game}`)).toBeVisible();
  await page.getByTestId(`game-grade-${grade}`).click();
  await page.getByTestId('game-grade-start').click();
}

export async function expectRaceCameraFramed(page) {
  const camera = page.getByTestId('game-camera');
  await expect(camera).toBeInViewport({ ratio: 1 });
  await expect.poll(() => camera.getByTestId('camera-world').evaluate(world => {
    const viewport = world.parentElement;
    const frame = viewport.getBoundingClientRect();
    const content = world.getBoundingClientRect();
    const clipsWorld = getComputedStyle(viewport).overflow === 'hidden';
    return clipsWorld && content.left <= frame.left + 2 && content.top <= frame.top + 2 &&
      content.right >= frame.right - 2 && content.bottom >= frame.bottom - 2;
  })).toBe(true);
}

export async function raceState(page) {
  return page.locator('[data-testid^="token-"]').first().evaluate(element => {
    let fiber = element[Object.keys(element).find(key => key.startsWith('__reactFiber$'))];
    while (fiber) {
      for (let hook = fiber.memoizedState, i = 0; hook && i < 100; hook = hook.next, i++) {
        const value = hook.memoizedState;
        if (typeof value?.getSnapshot === 'function' && typeof value?.startGame === 'function') return value.getSnapshot();
      }
      fiber = fiber.return;
    }
    return null;
  });
}
