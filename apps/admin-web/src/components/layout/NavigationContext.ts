import { createContext } from 'react';

// Drawer state is presentation only; authentication remains in AuthContext.
export const AdminNavigation = createContext({ open: false, show: () => {} });
