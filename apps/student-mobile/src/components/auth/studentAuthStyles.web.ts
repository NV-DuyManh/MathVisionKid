export const studentAuthStyles = `
  .student-auth {
    --auth-ink: #1c174c;
    --auth-purple: #713CF7;
    --auth-gold: #FFD044;
    --auth-line: #e2d9f3;
    display: grid;
    flex: 1;
    grid-template-columns: minmax(0, 54fr) minmax(0, 46fr);
    min-block-size: 0;
    overflow: auto;
    background: #F6F3FF;
    color: var(--auth-ink);
    font-family: NunitoRegular, system-ui, sans-serif;
  }

  .student-auth-hero {
    position: relative;
    isolation: isolate;
    overflow: hidden;
    margin: clamp(16px, 3vw, 50px) 0 clamp(16px, 3vw, 50px) clamp(16px, 3vw, 50px);
    border-radius: 36px;
    min-height: 680px;
    padding: 26px clamp(30px, 4vw, 64px) 120px;
    background: radial-gradient(ellipse 72% 26% at 3% 110%, #BA9AFF 0 64%, transparent 65%),
      radial-gradient(ellipse 82% 26% at 100% 104%, #AC8BF2 0 62%, transparent 63%),
      linear-gradient(133deg, #341885, #3E35D6 48%, #8147EE 100%);
    color: #fff;
  }

  .student-auth-hero::before,
  .student-auth-hero::after {
    content: "";
    position: absolute;
    z-index: -1;
    display: block;
    inline-size: clamp(240px, 28vw, 448px);
    aspect-ratio: 1;
    border-radius: 50%;
    background: #a86bfb33;
  }

  .student-auth-hero::before { inset: auto -10% 84% auto; }
  .student-auth-hero::after { inset: 88% auto auto -23%; background: #83a4ff33; }

  .student-auth-brand {
    display: flex;
    align-items: center;
    gap: .32em;
    font-size: clamp(20px, 1.5vw, 26px);
    font-family: NunitoBlack, system-ui, sans-serif;
  }

  .student-auth-brand > span:first-child {
    display: grid;
    place-items: center;
    inline-size: 22px;
    block-size: 34px;
    border-radius: 14px;
    margin-inline-end: 4px;
    background: var(--auth-gold);
    color: var(--auth-purple);
  }

  .student-auth-brand-accent, .student-auth-slogan span { color: var(--auth-gold); }

  .student-auth-intro { position: relative; z-index: 1; padding-block-start: clamp(36px, 8vh, 82px); }
  .student-auth-slogan { margin: 0; font-family: NunitoBlack, system-ui, sans-serif; font-size: clamp(39px, 4.1vw, 66px); line-height: 1.09; letter-spacing: -.035em; }
  .student-auth-description { margin: 24px 0; max-width: 470px; font-size: clamp(14px, 1.15vw, 17px); line-height: 1.75; color: #f2eaff; }
  .student-auth-highlights { display: flex; flex-wrap: wrap; list-style: none; gap: 8px; padding: 0; margin: 0; }
  .student-auth-highlights li { display: flex; align-items: center; gap: 7px; border: 1px solid #ffffff59; border-radius: 12px; background: #ffffff15; padding: 10px; font-size: 13px; color: #fff; }
  .student-auth-highlights li > span { color: var(--auth-gold); }

  .student-auth-art {
    position: absolute;
    inset: auto clamp(12px, 2.6vw, 46px) clamp(28px, 7vh, 75px) auto;
    width: min(51%, 465px);
    transform: rotate(-4deg);
  }

  .student-auth-art::before {
    content: "";
    position: absolute;
    inset: 15% -3% 37%;
    border-block: 2px solid #c398f96b;
    transform: skewY(-12deg);
  }

  .student-auth-art > span {
    display: block;
    position: relative;
    margin-block-start: -12px;
    padding: 10px 16px;
    border: 1px solid #ffffff45;
    border-radius: 14px;
    background: #ffffff27;
    font-size: 14px;
    font-weight: 900;
    color: #ffebae;
    transform: rotate(12deg);
  }

  .student-auth-art > span:last-child { transform: rotate(-5deg); }
  .student-auth-main { box-sizing: border-box; display: grid; align-items: center; justify-items: center; min-width: 0; padding: clamp(16px, 3vw, 50px); }
  .student-auth-main > div { width: 100%; max-width: 580px; padding: clamp(20px, 3.1vw, 48px); background: white; border: 1px solid var(--auth-line); border-radius: 34px; box-shadow: 0 12px 45px #32187414; }

  .student-auth [data-student-auth-field="true"] {
    gap: 10px;
    background: #f8f6fc;
    border-color: var(--auth-line);
    border-radius: 17px;
  }

  .student-auth [data-student-auth-field="true"]:focus-within {
    border-color: var(--auth-purple);
    box-shadow: 0 0 0 3px #7449df33;
  }

  .student-auth [data-student-auth-field="true"] input:focus,
  .student-auth [data-student-auth-field="true"] input:focus-visible {
    outline: none;
    box-shadow: none;
  }

  .student-auth [data-student-auth-field="true"] [role="button"] { border-radius: 9px; }
  .student-auth [data-student-primary="true"] {
    border: 0;
    border-radius: 24px;
    background: linear-gradient(110deg, #5930D9, #7D35E4);
  }

  .student-auth [data-student-primary="true"][aria-disabled="true"] { opacity: .74; }
  .student-auth [data-student-primary="true"]:not([aria-busy="true"]) > div { flex-direction: row-reverse; gap: 9px; }
  .student-auth [data-student-primary="true"]:not([aria-busy="true"]) > div > div:first-child { margin-inline: 0; }
  .student-auth [data-student-auth-card="true"] [role="heading"] { font-size: clamp(27px, 2.2vw, 35px); line-height: 1.25; }

  @media (min-width: 520px) and (max-width: 839px), (min-width: 1080px) {
    .student-auth [data-student-auth-form="register"] { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 12px; }
    .student-auth [data-student-auth-form="register"] > [data-student-auth-full-row="true"],
    .student-auth [data-student-auth-form="register"] > [role="button"] { grid-column: 1 / -1; }
  }

  @media (max-width: 1039px) {
    .student-auth-main { padding-inline: 32px; }
  }

  @media (max-width: 839px) {
    .student-auth { grid-template-columns: minmax(0, 1fr); grid-template-rows: max-content 1fr; }
    .student-auth-hero { min-height: 0; margin: 12px 12px 0; border-radius: 24px; padding: 20px 26px 24px; }
    .student-auth-intro { padding-block-start: 18px; }
    .student-auth-slogan { font-size: 30px; }
    .student-auth-kicker, .student-auth-description, .student-auth-highlights, .student-auth-art { display: none; }
    .student-auth-main { padding: 14px 12px 28px; }
    .student-auth-main > div { padding: 18px; border-radius: 24px; }
  }

  @media (max-width: 430px) {
    .student-auth-hero { padding: 18px 20px 21px; }
    .student-auth-slogan { font-size: 28px; }
  }

  @media (forced-colors: active) {
    .student-auth [data-student-auth-field="true"]:focus-within { outline: 2px solid Highlight; outline-offset: 2px; }
    .student-auth [data-student-primary="true"] { border: 1px solid ButtonText; }
  }
`;
