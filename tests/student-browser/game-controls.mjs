import { expect } from '@playwright/test';

export async function chooseTrainingGrade(page,game,grade=5) {
  if(!['race-to-finish','terrain-racing','energy-defense'].includes(game))return;
  await expect(page.getByTestId(`grade-selection-${game}`)).toBeVisible();
  await page.getByTestId(`game-grade-${grade}`).click();
  await page.getByTestId('game-grade-start').click();
}
