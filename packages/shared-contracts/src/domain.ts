export interface User {
  userId: string;
  email: string;
  role: 'STUDENT' | 'TEACHER' | 'ADMIN';
  createdAt: string;
}

export interface Student extends User {
  role: 'STUDENT';
  firstName: string;
  lastName: string;
  gradeLevel?: string;
}

export interface Teacher extends User {
  role: 'TEACHER';
  title: string;
  firstName: string;
  lastName: string;
  schoolId?: string;
}

export interface ClassRoom {
  classId: string;
  teacherId: string;
  name: string;
  gradeLevel: string;
  studentCount: number;
  createdAt: string;
}
