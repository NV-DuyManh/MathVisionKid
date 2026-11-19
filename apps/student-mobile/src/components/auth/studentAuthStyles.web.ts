import { STUDENT_WEB } from '../../constants/studentWebDesign';

export const studentAuthStyles = `
  .student-auth {
    --auth-ink: ${STUDENT_WEB.ink};
    --auth-purple: ${STUDENT_WEB.brand};
    --auth-gold: ${STUDENT_WEB.gold};
    --auth-line: ${STUDENT_WEB.border};
    display: flex;
    flex: 1;
    min-block-size: 0;
    overflow: auto;
    background: ${STUDENT_WEB.background};
    color: var(--auth-ink);
    font-family: NunitoRegular, system-ui, sans-serif;
  }

  .student-auth-layout {
    flex: 1;
    min-width: 0;
    box-sizing: border-box;
    display: grid;
    grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
    gap: 20px;
    align-items: stretch;
    align-self: flex-start;
    max-width: 1070px;
    margin-inline: auto;
    margin-block: auto;
    padding: 24px;
  }

  .student-auth-hero {
    position: relative;
    isolation: isolate;
    overflow: hidden;
    border-radius: 30px;
    min-height: 485px;
    box-sizing: border-box;
    padding: 32px 34px 180px;
    background:
      radial-gradient(ellipse 42% 23% at 3% 108%, #DCC7FB 0 70%, transparent 71%),
      radial-gradient(ellipse 55% 29% at 71% 111%, #CDB1FA 0 75%, transparent 76%),
      radial-gradient(ellipse 30% 25% at 106% 99%, #DCC7FB 0 71%, transparent 72%),
      radial-gradient(ellipse 61% 60% at 91% 3%, #9D61FF9C, transparent 66%),
      linear-gradient(147deg, #3C28BB, #6051E9 55%, #704AE5);
    color: #fff;
  }

  .student-auth-brand {
    display: flex;
    align-items: center;
    gap: 8px;
    font: 20px NunitoBlack, system-ui, sans-serif;
  }
  .student-auth-intro { position: relative; z-index: 1; padding-block-start: 20px; }
  .student-auth-slogan { margin: 0; font: clamp(37px, 3.35vw, 52px)/1.075 NunitoBlack, system-ui, sans-serif; letter-spacing: -.035em; }
  .student-auth-slogan span { color: var(--auth-gold); }
  .student-auth-description { margin: 14px 0 0; max-width: 280px; font-size: 15px; line-height: 1.47; color: #fff; }
  .student-auth-art {
    position: absolute;
    z-index: 1;
    right: 3%;
    bottom: 3%;
    inline-size: min(58%, 312px);
    pointer-events: none;
  }
  .student-auth-math {
    position:absolute;
    bottom: 21%;
    left: 12%;
    display:grid;
    gap:5px;
    justify-items:center;
    padding: 9px 13px;
    color:#E9FAFF;
    font-size: 13px;
    border:1px solid #9BE6FF;
    border-radius:11px;
    background:#264CB2;
    box-shadow: 0 0 16px #77C9FF70;
    transform:rotate(-10deg);
  }

  .student-auth-main { display: flex; min-width: 0; }
  .student-auth-main > div {
    box-sizing: border-box;
    width: 100%;
    align-self:stretch;
    justify-content:center;
    margin: 0;
    max-width: none;
    padding: 25px 27px;
    background: white;
    border: 1px solid var(--auth-line);
    border-radius: 30px;
    box-shadow: 0 12px 34px #32187413;
  }
  .student-auth [data-student-auth-form] > div { margin-bottom: 11px; }
  .student-auth [data-student-auth-form] > [role="button"]:last-child { margin-top: 2px; }
  .student-auth [data-student-auth-field="true"] {
    gap: 8px;
    min-height: 46px;
    padding-inline: 11px;
    background: #F2EDF9;
    border-color: var(--auth-line);
    border-radius: 17px;
  }
  .student-auth [data-student-auth-field="true"] input { min-height: 44px; font-size: 15px; }
  .student-auth [data-student-auth-field="true"]:focus-within {
    border-color: var(--auth-purple);
    box-shadow: 0 0 0 3px #7449df33;
  }
  .student-auth [data-student-auth-field="true"] input:focus,
  .student-auth [data-student-auth-field="true"] input:focus-visible { outline: none; box-shadow: none; }
  .student-auth [data-student-auth-field="true"] [role="button"] { border-radius: 9px; }
  .student-auth [data-student-primary="true"] {
    min-height: 48px;
    border: 0;
    border-radius: 24px;
    background: linear-gradient(105deg, #6034DF, #883EE9);
  }
  .student-auth [data-student-primary="true"][aria-disabled="true"] { opacity: .74; }
  .student-auth [data-student-primary="true"]:not([aria-busy="true"]) > div { flex-direction: row-reverse; gap: 9px; }
  .student-auth [data-student-primary="true"]:not([aria-busy="true"]) > div > div:first-child { margin-inline: 0; }

  @media (min-width: 520px) and (max-width: 839px), (min-width: 1060px) {
    .student-auth [data-student-auth-form="register"] { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 12px; }
    .student-auth [data-student-auth-form="register"] > [data-student-auth-full-row="true"],
    .student-auth [data-student-auth-form="register"] > [role="button"] { grid-column: 1 / -1; }
  }

  @media (max-width: 839px) {
    .student-auth-layout {
      display: flex;
      flex-direction: column;
      align-self: flex-start;
      width: 100%;
      max-width: 540px;
      margin-block: 0;
      padding: 12px;
      gap: 12px;
    }
    .student-auth-hero { min-height: 0; border-radius: 21px; padding: 15px 19px 20px; }
    .student-auth-brand { font-size: 17px; }
    .student-auth-intro { padding-block-start: 10px; }
    .student-auth-slogan { font-size: clamp(25px, 6.8vw, 32px); }
    .student-auth-description, .student-auth-art, .student-auth-math { display: none; }
    .student-auth-main > div { padding: 18px; border-radius: 21px; }
  }

  @media (forced-colors: active) {
    .student-auth [data-student-auth-field="true"]:focus-within { outline: 2px solid Highlight; outline-offset: 2px; }
    .student-auth [data-student-primary="true"] { border: 1px solid ButtonText; }
  }
`;
