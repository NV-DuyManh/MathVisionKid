import type { TeacherService } from './TeacherService';
import { MockTeacherService } from './MockTeacherService';
import { SpringTeacherService } from './SpringTeacherService';
import { useMocks } from '../../config/runtime';

export const AppTeacherService: TeacherService & { getMe?: () => Promise<any> } = useMocks ? MockTeacherService : SpringTeacherService;
