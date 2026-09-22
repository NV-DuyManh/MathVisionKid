import type { TeacherService } from './TeacherService';
import { MockTeacherService } from './MockTeacherService';
import { SpringTeacherService } from './SpringTeacherService';

const useMock = import.meta.env.VITE_USE_MOCK === 'true';

export const AppTeacherService: TeacherService & { getMe?: () => Promise<any> } = useMock ? MockTeacherService : SpringTeacherService;
