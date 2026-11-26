import React, { useEffect, useId, useRef, useState } from 'react';
import { useIsFocused } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import type { RecoveryDialogProps } from './RecoveryDialog';

const dialogStyles = `
.mvk-recovery-dialog { box-sizing: border-box; position: fixed; inset: 0; margin: auto;
  width: min(420px, calc(100% - 32px)); max-height: calc(100% - 32px); overflow: auto;
  overscroll-behavior: contain; padding: 28px 22px 22px; border: 1px solid #e8defa;
  border-radius: 22px; background: #fff; color: #211544; text-align: center;
  box-shadow: 0 18px 64px #20104540; font-family: NunitoRegular, sans-serif; }
.mvk-recovery-dialog::backdrop { background: #251748a6; }
.mvk-recovery-dialog h2 { margin: 14px 0 0; font: 24px/1.22 NunitoBold, sans-serif; }
.mvk-recovery-dialog p { margin: 8px 0 0; color: #5d5170; font-size: 15px; line-height: 1.5; }
.mvk-recovery-dialog button { cursor: pointer; }
.mvk-recovery-dialog button:focus-visible { outline: 2px solid #251748; outline-offset: 3px; }
.mvk-recovery-dialog button:disabled { cursor: default; opacity: .65; }
.mvk-recovery-close { position: absolute; inset-block-start: 8px; inset-inline-end: 8px;
  display: grid; place-items: center; width: 44px; height: 44px; border: 0;
  border-radius: 12px; color: #4c288e; background: transparent; }
.mvk-recovery-badge { display: grid; place-items: center; margin: auto; width: 48px; height: 48px;
  border-radius: 50%; color: #874c00; background: #fff0c8; }
.mvk-recovery-actions { display: grid; gap: 10px; margin-top: 20px; }
.mvk-recovery-actions button { min-height: 46px; padding: 10px 14px; border: 1px solid #6c36df;
  border-radius: 12px; background: #fff; color: #4e219e; font: 16px/1.4 NunitoBold, sans-serif; }
.mvk-recovery-actions .mvk-recovery-primary { background: #6c36df; color: #fff; }
`;

export function RecoveryDialog({ title, message, actions, fallback }: RecoveryDialogProps) {
  const id = useId();
  const focused = useIsFocused();
  const dialog = useRef<HTMLDialogElement>(null);
  const fallbackRoot = useRef<HTMLDivElement>(null);
  const restoreFallbackFocus = useRef(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const element = dialog.current;
    if (!focused || !element) return;
    if (typeof element.showModal !== 'function') {
      setDismissed(true);
      return;
    }
    element.showModal();
    element.querySelector<HTMLElement>('[data-initial-focus]')?.focus({ preventScroll: true });
    return () => { if (element.open) element.close(); };
  }, [focused]);

  useEffect(() => {
    if (dismissed && restoreFallbackFocus.current && document.activeElement === document.body) {
      fallbackRoot.current?.querySelector<HTMLElement>('[role="button"]:not([aria-disabled="true"])')?.focus({ preventScroll: true });
    }
  }, [dismissed]);

  const dismiss = (restoreFocus: boolean) => {
    restoreFallbackFocus.current = restoreFocus;
    dialog.current?.close();
    setDismissed(true);
  };
  if (!focused) return null;
  if (dismissed) return <div ref={fallbackRoot} style={{ display: 'contents' }}>{fallback}</div>;

  return <dialog ref={dialog} className="mvk-recovery-dialog" role="alertdialog" aria-modal="true"
    aria-labelledby={`${id}-title`} aria-describedby={message ? `${id}-message` : undefined}
    onCancel={event => { event.preventDefault(); dismiss(true); }}>
    <style>{dialogStyles}</style>
    <button className="mvk-recovery-close" type="button" aria-label="Đóng thông báo"
      data-initial-focus={!actions[0] || actions[0].disabled ? '' : undefined} onClick={() => dismiss(true)}>
      <Ionicons name="close" size={23} color="#4C288E" aria-hidden />
    </button>
    <span className="mvk-recovery-badge" aria-hidden="true"><Ionicons name="alert-circle-outline" size={28} color="#874C00" /></span>
    <h2 id={`${id}-title`}>{title}</h2>
    {message ? <p id={`${id}-message`}>{message}</p> : null}
    {actions.length ? <div className="mvk-recovery-actions">
      {actions.map((action, index) => <button key={action.accessibilityLabel || action.label} type="button"
        className={index === 0 ? 'mvk-recovery-primary' : undefined} aria-label={action.accessibilityLabel}
        data-initial-focus={index === 0 && !action.disabled ? '' : undefined} disabled={action.disabled}
        onClick={() => { dismiss(false); action.onPress(); }}>{action.label}</button>)}
    </div> : null}
  </dialog>;
}
