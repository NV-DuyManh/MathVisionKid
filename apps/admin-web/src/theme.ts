import { createTheme } from '@mui/material/styles';

export const adminTheme = createTheme({
  palette: {
    primary: {
      main: '#0F172A', // Slate Navy (Operational authority, high contrast)
      dark: '#020617',
      light: '#F8FAFC',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#2563EB', // Learning Blue (System accent)
      dark: '#1D4ED8',
      light: '#EFF6FF',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#F8FAFC',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#0F172A',
      secondary: '#475569',
    },
    divider: '#E2E8F0',
    success: {
      main: '#059669',
      dark: '#047857',
      light: '#ECFDF5',
      contrastText: '#FFFFFF',
    },
    error: {
      main: '#DC2626',
      dark: '#B91C1C',
      light: '#FEF2F2',
      contrastText: '#FFFFFF',
    },
    warning: {
      main: '#D97706',
      dark: '#B45309',
      light: '#FFFBEB',
      contrastText: '#FFFFFF',
    },
  },
  typography: {
    fontFamily: '"Plus Jakarta Sans", "Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif',
    h1: { fontSize: '2.5rem', fontWeight: 800, lineHeight: 1.18, letterSpacing: '-0.035em' },
    h2: { fontSize: '1.875rem', fontWeight: 800, lineHeight: 1.24, letterSpacing: '-0.03em' },
    h3: { fontSize: '1.5rem', fontWeight: 800, lineHeight: 1.28, letterSpacing: '-0.025em' },
    h4: { fontSize: '1.25rem', fontWeight: 800, lineHeight: 1.34, letterSpacing: '-0.02em' },
    h5: { fontSize: '1.1rem', fontWeight: 800, lineHeight: 1.38, letterSpacing: '-0.015em' },
    h6: { fontSize: '0.975rem', fontWeight: 700, lineHeight: 1.4 },
    subtitle1: { fontSize: '0.9375rem', fontWeight: 700, lineHeight: 1.5 },
    subtitle2: { fontSize: '0.8125rem', fontWeight: 700, lineHeight: 1.5 },
    body1: { fontSize: '0.9375rem', lineHeight: 1.62, color: '#334155' },
    body2: { fontSize: '0.84375rem', lineHeight: 1.55, color: '#475569' },
    caption: { fontSize: '0.75rem', lineHeight: 1.5, color: '#64748B' },
    button: { textTransform: 'none', fontWeight: 700, letterSpacing: 0 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#F8FAFC',
          color: '#0F172A',
        },
        '*, *::before, *::after': { boxSizing: 'border-box' },
        '::selection': { backgroundColor: '#E2E8F0', color: '#0F172A' },
        ':focus-visible': { outline: '2.5px solid #2563EB', outlineOffset: 2 },
        '@media (prefers-reduced-motion: reduce)': {
          '*, *::before, *::after': {
            animationDuration: '0.01ms !important',
            transitionDuration: '0.01ms !important',
            scrollBehavior: 'auto !important',
          },
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: {
          minHeight: 40,
          borderRadius: 10,
          padding: '8px 18px',
          fontWeight: 700,
          boxShadow: 'none',
          transition: 'all 180ms cubic-bezier(0.16, 1, 0.3, 1)',
        },
        contained: {
          backgroundColor: '#0F172A',
          color: '#FFFFFF',
          boxShadow: '0 1px 2px 0 rgba(15, 23, 42, 0.15)',
          '&:hover': {
            backgroundColor: '#1E293B',
            boxShadow: '0 4px 12px 0 rgba(15, 23, 42, 0.25)',
            transform: 'translateY(-1px)',
          },
          '&:active': {
            transform: 'translateY(0)',
          },
          '&.Mui-disabled': {
            backgroundColor: '#F1F5F9',
            color: '#94A3B8',
          },
        },
        outlined: {
          borderColor: '#CBD5E1',
          color: '#0F172A',
          backgroundColor: '#FFFFFF',
          boxShadow: '0 1px 2px 0 rgba(15, 23, 42, 0.03)',
          '&:hover': {
            borderColor: '#0F172A',
            backgroundColor: '#F8FAFC',
            color: '#0F172A',
            transform: 'translateY(-1px)',
          },
          '&:active': {
            transform: 'translateY(0)',
          },
        },
        sizeSmall: {
          minHeight: 34,
          padding: '5px 12px',
          fontSize: '0.8125rem',
          borderRadius: 8,
        },
        sizeLarge: {
          minHeight: 48,
          padding: '12px 24px',
          fontSize: '0.975rem',
          borderRadius: 12,
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          minHeight: 40,
          minWidth: 40,
          borderRadius: 10,
          transition: 'all 160ms ease',
          '&:focus-visible': { outline: '2.5px solid #2563EB', outlineOffset: 2 },
          '&:hover': { backgroundColor: '#F1F5F9' },
        },
      },
    },
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          borderRadius: 14,
          border: '1px solid #E2E8F0',
          boxShadow: '0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 4px 12px -2px rgba(15, 23, 42, 0.03)',
          backgroundImage: 'none',
          backgroundColor: '#FFFFFF',
          minWidth: 0,
          transition: 'box-shadow 200ms cubic-bezier(0.16, 1, 0.3, 1), border-color 200ms cubic-bezier(0.16, 1, 0.3, 1)',
        },
      },
    },
    MuiCardContent: {
      styleOverrides: {
        root: {
          padding: 22,
          '&:last-child': { paddingBottom: 22 },
        },
      },
    },
    MuiPaper: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: { backgroundImage: 'none' },
        outlined: {
          borderColor: '#E2E8F0',
          borderRadius: 14,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 7,
          fontWeight: 700,
          fontSize: '0.75rem',
          height: 26,
        },
      },
    },
    MuiTableContainer: {
      styleOverrides: {
        root: {
          maxWidth: '100%',
          overflowX: 'auto',
          borderRadius: 14,
          border: '1px solid #E2E8F0',
          boxShadow: '0 1px 3px 0 rgba(15, 23, 42, 0.03)',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          padding: '14px 18px',
          borderColor: '#F1F5F9',
          fontSize: '0.85rem',
        },
        head: {
          color: '#475569',
          fontWeight: 700,
          fontSize: '0.8125rem',
          letterSpacing: '0.02em',
          backgroundColor: '#F8FAFC',
          whiteSpace: 'nowrap',
          borderBottom: '1px solid #E2E8F0',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:last-child .MuiTableCell-root': { borderBottom: 0 },
          '&.MuiTableRow-hover:hover': { backgroundColor: '#F8FAFC' },
        },
      },
    },
    MuiTablePagination: {
      defaultProps: {
        labelRowsPerPage: 'Số dòng:',
        labelDisplayedRows: ({ from, to, count }) => `${from}–${to} / ${count}`,
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          backgroundColor: '#FFFFFF',
          transition: 'border-color 160ms ease, box-shadow 160ms ease',
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: '#CBD5E1',
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: '#94A3B8',
          },
          '&.Mui-focused': {
            boxShadow: '0 0 0 3px rgba(37, 99, 235, 0.12)',
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: '#2563EB',
            borderWidth: 1.5,
          },
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 18,
          border: '1px solid #E2E8F0',
          boxShadow: '0 24px 48px -12px rgba(15, 23, 42, 0.18)',
        },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          fontWeight: 800,
          color: '#0F172A',
          padding: '22px 26px 14px',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: { borderRadius: 10 },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          transition: 'all 140ms ease',
          '&.Mui-selected': {
            backgroundColor: 'rgba(15, 23, 42, 0.08)',
            color: '#0F172A',
            fontWeight: 800,
          },
          '&.Mui-selected:hover': {
            backgroundColor: 'rgba(15, 23, 42, 0.12)',
          },
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          fontSize: '0.75rem',
          borderRadius: 8,
          backgroundColor: '#0F172A',
          color: '#FFFFFF',
          padding: '6px 12px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        },
      },
    },
  },
});
