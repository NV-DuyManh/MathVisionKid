import { createTheme } from '@mui/material/styles';

/**
 * MathVision Kids — Teacher Portal Theme
 * Professional educational workspace: clean, friendly, efficient, and task-oriented.
 * Distinct Emerald Green (#059669) pedagogical authority combined with MathVision Kids DNA.
 */
export const theme = createTheme({
  palette: {
    primary: {
      main: '#059669', // Emerald Green (Authority, evaluation, pedagogical growth)
      dark: '#047857',
      light: '#ECFDF5',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#0F172A', // Slate Navy
      dark: '#020617',
      light: '#F1F5F9',
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
    success: {
      main: '#059669',
      dark: '#047857',
      light: '#ECFDF5',
      contrastText: '#FFFFFF',
    },
    info: {
      main: '#2563EB',
      dark: '#1D4ED8',
      light: '#EFF6FF',
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
        '::selection': { backgroundColor: '#ECFDF5', color: '#047857' },
        ':focus-visible': { outline: '2.5px solid #059669', outlineOffset: 2 },
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
          borderRadius: 10,
          minHeight: 40,
          padding: '8px 18px',
          fontWeight: 700,
          boxShadow: 'none',
          transition: 'all 180ms cubic-bezier(0.16, 1, 0.3, 1)',
        },
        contained: {
          backgroundColor: '#059669',
          color: '#FFFFFF',
          boxShadow: '0 1px 2px 0 rgba(5, 150, 105, 0.15)',
          '&:hover': {
            backgroundColor: '#047857',
            boxShadow: '0 4px 12px 0 rgba(5, 150, 105, 0.25)',
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
            borderColor: '#059669',
            backgroundColor: '#ECFDF5',
            color: '#059669',
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
          minWidth: 40,
          minHeight: 40,
          borderRadius: 10,
          transition: 'all 160ms ease',
          '&:focus-visible': { outline: '2.5px solid #059669', outlineOffset: 2 },
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
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: '#F8FAFC',
          '& .MuiTableCell-head': {
            color: '#475569',
            fontWeight: 700,
            fontSize: '0.8125rem',
            letterSpacing: '0.02em',
            whiteSpace: 'nowrap',
            borderBottom: '1px solid #E2E8F0',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderColor: '#F1F5F9',
          padding: '14px 18px',
          fontSize: '0.875rem',
        },
        head: {
          padding: '12px 18px',
          whiteSpace: 'nowrap',
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
        labelDisplayedRows: ({ from, to, count }) =>
          `${from}–${to} / ${count === -1 ? `hơn ${to}` : count}`,
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          backgroundColor: '#FFFFFF',
          borderRadius: 10,
          transition: 'border-color 160ms ease, box-shadow 160ms ease',
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: '#CBD5E1',
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: '#94A3B8',
          },
          '&.Mui-focused': {
            boxShadow: '0 0 0 3px rgba(5, 150, 105, 0.12)',
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: '#059669',
            borderWidth: 1.5,
          },
        },
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        root: {
          color: '#64748B',
          fontSize: '0.875rem',
        },
      },
    },
    MuiFormHelperText: {
      styleOverrides: {
        root: {
          marginLeft: 2,
          marginTop: 6,
          fontSize: '0.75rem',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          alignItems: 'flex-start',
        },
        standard: {
          '&.MuiAlert-colorInfo': {
            backgroundColor: '#ECFDF5',
            color: '#047857',
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: { minHeight: 44 },
        indicator: { height: 2.5, borderRadius: '2px 2px 0 0', backgroundColor: '#059669' },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 700,
          minHeight: 44,
          fontSize: '0.875rem',
          color: '#64748B',
          transition: 'color 140ms ease',
          '&.Mui-selected': { color: '#059669' },
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
          padding: '22px 26px 14px',
          color: '#0F172A',
        },
      },
    },
    MuiDialogContent: {
      styleOverrides: {
        root: {
          padding: '14px 26px 22px',
        },
      },
    },
    MuiDialogActions: {
      styleOverrides: {
        root: {
          padding: '14px 26px 22px',
          gap: 10,
          flexWrap: 'wrap',
          borderTop: '1px solid #F1F5F9',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          transition: 'all 140ms ease',
          '&.Mui-selected': {
            backgroundColor: 'rgba(5, 150, 105, 0.08)',
            color: '#059669',
            fontWeight: 800,
          },
          '&.Mui-selected:hover': {
            backgroundColor: 'rgba(5, 150, 105, 0.12)',
          },
        },
      },
    },
    MuiSkeleton: {
      styleOverrides: {
        root: { backgroundColor: '#F1F5F9' },
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

export default theme;
