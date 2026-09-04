export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ConfidenceBundle {
  recognition: number;
  structure: number;
  diagnosis: number;
  overall?: number;
}

export interface Evidence {
  evidenceId: string;
  type: string; // e.g., 'COLUMN_VALIDATION'
  boundingBox?: BoundingBox;
  placeValue?: string; // e.g., 'UNITS', 'TENS'
  ruleId?: string; // e.g., 'ADD_COLUMN_WITH_CARRY'
  observedText?: string;
  expectedRelation?: string;
  observedRelation?: string;
  confidence: number;
  description?: string;
}
