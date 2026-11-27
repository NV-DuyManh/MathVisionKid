import type { ReactNode } from 'react';
import type { RecoveryAction } from './RecoveryNotice';

export type RecoveryDialogProps = {
  title: string;
  message?: string;
  actions: RecoveryAction[];
  fallback: ReactNode;
};

export function RecoveryDialog({ fallback }: RecoveryDialogProps) {
  return fallback;
}
