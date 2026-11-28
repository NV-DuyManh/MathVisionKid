// Desktop presentation only; native screens and game state remain in the package.
export const GAME_DESKTOP_STYLES = `
@media (pointer: fine) {
  [data-game="race-to-finish"] [data-testid="game-camera"] {
    max-width: 100%;
    max-height: 100%;
    background: radial-gradient(ellipse at 50% 0, #a9754338, transparent 70%),
      repeating-linear-gradient(0deg, #f2d1a408 0 1px, transparent 1px 6px),
      linear-gradient(110deg, #392a24, #231d23 50%, #392a24);
  }
  [data-game="race-to-finish"] [data-testid="race-board"] {
    border-radius: 12px;
    box-shadow: 0 8px 28px #0f0b12aa, 0 0 0 1px #e9b97355;
  }
  [data-game="terrain-racing"] {
    background: radial-gradient(ellipse at 50% 25%, #c58c5738, transparent 65%),
      repeating-linear-gradient(135deg, #e8c68a08 0 2px, transparent 2px 30px),
      linear-gradient(90deg, #201e25, #494039 50%, #201e25);
  }
  [data-game="terrain-racing"] > div:last-child {
    box-shadow: 0 0 0 1px #efd19c44, 0 0 64px #d59e6533, 0 18px 80px #100e15;
  }
  [data-game="terrain-racing"] [data-testid^="supercar-state-"] > div:first-child {
    background: linear-gradient(90deg, #2b252a, #47392f, #2b252a);
  }
}
@media (min-width: 1000px) and (pointer: fine) {
  [data-testid="energy-layout"] {
    display: grid;
    grid-template-columns: minmax(0, 1fr) clamp(240px, 29%, 365px);
    align-items: start !important;
    gap: 12px !important;
  }
  [data-testid="energy-layout"] > div { width: auto; }
  [data-testid="energy-question-column"] { min-width: 0; }
  [data-testid="energy-inventory"] {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  [data-testid^="energy-crystal-"] {
    width: auto !important;
    min-width: 0 !important;
    min-height: 44px !important;
    padding: 4px !important;
    flex-direction: row !important;
    gap: 5px !important;
  }
  [data-testid^="energy-crystal-"] > div:first-child svg {
    width: 19px;
    height: 19px;
    display: block;
  }
  [data-testid^="energy-crystal-"] [dir="auto"] { font-size: 15px !important; line-height: 17px !important; }
  [data-game="planet-rescue"] [data-testid="rescue-page"] > div {
    padding: 12px 20px 16px !important;
    max-width: 1600px;
  }
  [data-game="planet-rescue"] [data-testid="rescue-header"] { margin-bottom: 10px; }
  [data-game="planet-rescue"] [data-testid="rescue-header"] [role="button"] { min-height: 44px; }
  [data-game="planet-rescue"] [data-testid="rescue-mode-bar"] { margin-bottom: 10px; padding: 3px; }
  [data-game="planet-rescue"] [data-testid="rescue-mode-bar"] [role="button"] > div { padding: 5px 12px; }
  [data-game="planet-rescue"] [data-testid="rescue-mission"] { margin-bottom: 10px; }
  [data-game="planet-rescue"] [data-testid="rescue-workbench"] { gap: 18px; align-items: flex-start; }
  [data-game="planet-rescue"] [data-testid="rescue-flight-column"] { flex: 1; min-width: 0; }
  [data-game="planet-rescue"] [data-testid="rescue-lab-column"] { flex: 1.25; width: auto; min-width: 0; }
  [data-game="planet-rescue"] [data-testid="rescue-arena"] { height: clamp(220px, 36vh, 390px) !important; }
  [data-game="planet-rescue"] [data-testid="rescue-deck-heading"] { margin-top: 12px; margin-bottom: 8px; }
  [data-game="planet-rescue"] [data-testid^="rescue-card-"] > div { padding: 8px; gap: 5px; }
  [data-game="planet-rescue"] [data-testid="rescue-pilot-note"], [data-game="planet-rescue"] [data-testid="rescue-page-footer"],
  [data-game="planet-rescue"] [data-testid="rescue-lab-footer"] { display: none; }
  [data-game="planet-rescue"] [data-testid="rescue-math-panel"], [data-game="planet-rescue"] [data-testid="rescue-flight-panel"] {
    min-height: 0;
    padding: 14px;
    border-radius: 20px;
  }
  [data-game="planet-rescue"] [data-testid="rescue-panel-heading"] { display: none; }
  [data-game="planet-rescue"] [data-testid="rescue-sources"] { padding-top: 0; gap: 10px; }
  [data-game="planet-rescue"] [data-testid^="rescue-source-"] { padding: 8px 10px; }
  [data-game="planet-rescue"] [data-testid^="rescue-source-values-"] { margin: 5px 0; padding: 0; min-height: 0; }
  [data-game="planet-rescue"] [data-testid^="rescue-source-values-"] [dir="auto"] { font-size: 20px !important; line-height: 24px !important; }
  [data-game="planet-rescue"] [data-testid="rescue-frequency"] { padding: 5px 0; }
  [data-game="planet-rescue"] [data-testid="rescue-sum"] { padding: 5px; margin-top: 6px; }
  [data-game="planet-rescue"] [data-testid="rescue-task"] { margin-top: 10px; gap: 4px; }
  [data-game="planet-rescue"] [data-testid="rescue-task"] > div:last-child { font-size: 21px; line-height: 27px; }
  [data-game="planet-rescue"] [data-testid="rescue-hint"] { margin-top: 5px; font-size: 13px; line-height: 19px; }
  [data-game="planet-rescue"] [data-testid="rescue-equation"] { margin-top: 6px; padding: 5px 0; }
  [data-game="planet-rescue"] [data-testid="rescue-options"] { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; }
  [data-game="planet-rescue"] [data-testid="rescue-options"] > div { width: auto !important; min-height: 48px !important; }
  [data-game="planet-rescue"] [data-testid="rescue-options"] [role="button"] > div { padding: 8px; }
  [data-game="planet-rescue"] [data-testid="rescue-feedback"] { margin-top: 10px; padding: 9px; }
  [data-game="planet-rescue"] [data-testid="rescue-log"] { padding-top: 8px; gap: 4px; }
  [data-game="planet-rescue"] [data-testid="rescue-fire"] { min-height: 48px; }
}
`;
