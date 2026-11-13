import { createTheme } from '@mui/material/styles';
import { WEB_DESIGN } from '../../../packages/ui-brand/src/web-design';

const { colors, focus, motion, roles, typography, components } = WEB_DESIGN;
const teacher = roles.teacher;
const workspaceBackground = '#F6F8F6';
const focusRing = `${focus.width}px solid ${focus.color}`;

export const theme = createTheme({
  palette: {
    primary: {
      main: teacher.action,
      dark: '#065F46',
      light: teacher.tint,
      contrastText: colors.white,
    },
    secondary: {
      main: '#0F172A', // Slate Navy
      dark: '#020617',
      light: '#F1F5F9',
      contrastText: '#FFFFFF',
    },
    background: {
      default: workspaceBackground,
      paper: colors.white,
    },
    text: {
      primary: colors.ink,
      secondary: colors.mutedInk,
    },
    divider: colors.line,
    error: {
      main: '#DC2626',
      dark: '#B91C1C',
      light: '#FEF2F2',
      contrastText: '#FFFFFF',
    },
    warning: {
      main: '#A64F08',
      dark: '#B45309',
      light: '#FFFBEB',
      contrastText: '#FFFFFF',
    },
    success: {
      main: teacher.action,
      dark: '#065F46',
      light: teacher.tint,
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
    fontFamily: typography.body,
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
  shape: { borderRadius: components.workspacePanel.radius },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: workspaceBackground,
          color: colors.ink,
        },
        ':root': {
          '--teacher-divider': colors.line,
          '--teacher-paper': colors.paper,
          '--teacher-paper-line': colors.paperLine,
          '--teacher-accent': teacher.action,
          '--teacher-tint': teacher.tint,
        },
        '*, *::before, *::after': { boxSizing: 'border-box' },
        '::selection': { backgroundColor: '#ECFDF5', color: '#047857' },
        ':focus-visible, .MuiButtonBase-root.Mui-focusVisible': { outline: focusRing, outlineOffset: focus.offset },
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
          borderRadius: components.action.radius,
          minHeight: components.action.minHeight,
          padding: '8px 18px',
          fontWeight: 700,
          boxShadow: 'none',
          transition: `background-color ${motion.press}ms ease, color ${motion.press}ms ease, border-color ${motion.press}ms ease`,
        },
        contained: {
          boxShadow: 'none',
        },
        outlined: {
          '&.MuiButton-colorPrimary': {
            borderColor: '#CBD5E1',
            color: colors.ink,
            backgroundColor: colors.white,
          },
          '&.MuiButton-colorPrimary:hover': {
            borderColor: teacher.action,
            color: teacher.action,
            backgroundColor: teacher.tint,
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
          '&:focus-visible': { outline: focusRing, outlineOffset: focus.offset },
          '&:hover': { backgroundColor: '#F1F5F9' },
        },
      },
    },
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          borderRadius: components.workspacePanel.radius,
          border: `1px solid ${colors.line}`,
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
          borderColor: colors.line,
          borderRadius: components.workspacePanel.radius,
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
          borderRadius: components.workspacePanel.radius,
          border: `1px solid ${colors.line}`,
          '&:focus-visible': { outline: focusRing, outlineOffset: -focus.width },
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: '#F2F6F3',
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
          padding: '12px 16px',
          fontSize: '0.875rem',
        },
        head: {
          padding: '10px 16px',
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
            borderColor: teacher.action,
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
        indicator: { height: 2.5, borderRadius: '2px 2px 0 0', backgroundColor: teacher.action },
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
          '&.Mui-selected': { color: teacher.action },
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
            color: teacher.action,
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
