import { createTheme } from '@mui/material/styles';
import { WEB_DESIGN } from '../../../packages/ui-brand/src/web-design';

const { colors, components, focus, motion, radii, roles, typography } = WEB_DESIGN;
const admin = roles.admin;

export const adminTheme = createTheme({
  palette: {
    primary: {
      main: admin.action,
      dark: '#3730A3',
      light: admin.tint,
      contrastText: colors.white,
    },
    secondary: {
      main: colors.blue,
      dark: '#1D4ED8',
      light: colors.blueLight,
      contrastText: colors.white,
    },
    background: {
      default: '#F6F7FC',
      paper: colors.white,
    },
    text: {
      primary: colors.ink,
      secondary: colors.mutedInk,
    },
    divider: colors.line,
    success: {
      main: colors.green,
      dark: '#047857',
      light: '#ECFDF5',
      contrastText: colors.white,
    },
    error: {
      main: '#DC2626',
      dark: '#B91C1C',
      light: '#FEF2F2',
      contrastText: colors.white,
    },
    warning: {
      main: '#B45309',
      dark: '#B45309',
      light: '#FFFBEB',
      contrastText: colors.white,
    },
  },
  typography: {
    fontFamily: typography.body,
    h1: { fontSize: '2.5rem', fontWeight: 800, lineHeight: 1.18, letterSpacing: '-0.035em' },
    h2: { fontSize: '1.75rem', fontWeight: 800, lineHeight: 1.24, letterSpacing: '-0.03em' },
    h3: { fontSize: '1.5rem', fontWeight: 800, lineHeight: 1.28, letterSpacing: '-0.025em' },
    h4: { fontSize: '1.25rem', fontWeight: 800, lineHeight: 1.34, letterSpacing: '-0.02em' },
    h5: { fontSize: '1.1rem', fontWeight: 800, lineHeight: 1.38, letterSpacing: '-0.015em' },
    h6: { fontSize: '0.975rem', fontWeight: 700, lineHeight: 1.4 },
    subtitle1: { fontSize: '0.9375rem', fontWeight: 700, lineHeight: 1.5 },
    subtitle2: { fontSize: '0.8125rem', fontWeight: 700, lineHeight: 1.5 },
    body1: { fontSize: '0.9375rem', lineHeight: 1.62, color: '#334155' },
    body2: { fontSize: '0.84375rem', lineHeight: 1.55, color: colors.mutedInk },
    caption: { fontSize: '0.75rem', lineHeight: 1.5, color: '#64748B' },
    button: { textTransform: 'none', fontWeight: 700, letterSpacing: 0 },
  },
  shape: { borderRadius: radii.panel },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#F6F7FC',
          color: colors.ink,
        },
        ':root': {
          '--admin-ink': colors.ink,
          '--admin-action': admin.action,
          '--admin-tint': admin.tint,
          '--admin-line': colors.line,
          '--admin-paper': colors.paper,
          '--admin-paper-line': colors.paperLine,
          '--admin-panel-radius': `${radii.panel}px`,
        },
        '*, *::before, *::after': { boxSizing: 'border-box' },
        '::selection': { backgroundColor: admin.tint, color: colors.ink },
        ':focus-visible': { outline: `${focus.width}px solid ${focus.color}`, outlineOffset: focus.offset },
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
          minHeight: components.action.minHeight,
          borderRadius: radii.control,
          padding: '8px 18px',
          fontWeight: 700,
          transition: `background-color ${motion.press}ms ease, border-color ${motion.press}ms ease, color ${motion.press}ms ease`,
          '&.Mui-focusVisible': { outline: `${focus.width}px solid ${focus.color}`, outlineOffset: focus.offset },
        },
        outlined: {
          '&.MuiButton-colorPrimary': { borderColor: '#BFC2DF', backgroundColor: colors.white },
          '&.MuiButton-colorPrimary:hover': { borderColor: admin.action, backgroundColor: admin.tint },
        },
        sizeSmall: {
          minHeight: 36,
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
          transition: `background-color ${motion.press}ms ease, color ${motion.press}ms ease`,
          '&.Mui-focusVisible': { outline: `${focus.width}px solid ${focus.color}`, outlineOffset: focus.offset },
          '&:hover': { backgroundColor: '#F1F5F9' },
        },
      },
    },
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          borderRadius: radii.panel,
          border: '1px solid #E2E8F0',
          backgroundImage: 'none',
          backgroundColor: colors.white,
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
          borderColor: colors.line,
          borderRadius: radii.panel,
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
          borderRadius: radii.panel,
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
          fontSize: '0.875rem',
          fontVariantNumeric: 'tabular-nums',
        },
        head: {
          padding: '12px 18px',
          color: colors.mutedInk,
          fontWeight: 700,
          fontSize: '0.8125rem',
          letterSpacing: '0.02em',
          backgroundColor: '#F6EDCE',
          whiteSpace: 'nowrap',
          borderBottom: '1px solid #E2E8F0',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:last-child .MuiTableCell-root': { borderBottom: 0 },
          '&.MuiTableRow-hover:hover, &.MuiTableRow-hover:focus-within': { backgroundColor: admin.tint },
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
          borderRadius: 10,
          backgroundColor: colors.white,
          transition: 'border-color 160ms ease, box-shadow 160ms ease',
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: '#CBD5E1',
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: '#94A3B8',
          },
          '&.Mui-focused': {
            boxShadow: '0 0 0 3px rgba(67, 56, 202, 0.12)',
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: admin.action,
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
          color: colors.ink,
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
          transition: `background-color ${motion.press}ms ease, color ${motion.press}ms ease`,
          '&.Mui-selected': {
            backgroundColor: admin.tint,
            color: admin.action,
            fontWeight: 800,
          },
          '&.Mui-selected:hover': {
            backgroundColor: '#E2E0FF',
          },
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          fontSize: '0.75rem',
          borderRadius: 8,
          backgroundColor: colors.ink,
          color: colors.white,
          padding: '6px 12px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        },
      },
    },
  },
});
