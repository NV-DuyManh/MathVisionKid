export interface AuditEvent {
  auditEventId: string;
  entityType: 'SUBMISSION' | 'BATCH' | 'ASSIGNMENT' | 'CLASSROOM';
  entityId: string;
  action: 'SUBMISSION_CREATED' | 'IMAGE_UPLOADED' | 'AI_PROCESSING_STARTED' | 'AI_RESULT_CREATED' | 'TOKEN_CONFIRMED' | 'RETRY_REQUESTED' | 'TEACHER_APPROVED' | 'TEACHER_OVERRIDDEN' | 'IMAGE_RETAKEN';
  actorType: 'SYSTEM' | 'STUDENT' | 'TEACHER';
  actorId: string;
  timestamp: string;
  metadata?: Record<string, any>;
}
