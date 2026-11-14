import React from 'react';
import type { TrainingGameId } from '@mathvisionkid/training-games';

export function enterGameDisplay(_gameId: TrainingGameId) {}

export function GameDisplay({ children }: { gameId: TrainingGameId; children: React.ReactNode; onExit: () => void }) {
  return <>{children}</>;
}
