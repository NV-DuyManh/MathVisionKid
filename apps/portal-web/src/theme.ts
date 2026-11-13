import { createTheme } from '@mui/material/styles';
import { WEB_DESIGN } from '../../../packages/ui-brand/src/web-design';

/**
 * MathVision Kids — Kid-First Premium Design System Theme
 * Modern children's EdTech: playful + delightful + intuitive + modern + premium + safe + educational.
 * Inspired by tactile digital math notebooks, cheerful companion star mascot, and clear Vietnamese typography.
 */
export const theme = createTheme({
  palette: {
    primary: {
      main: WEB_DESIGN.roles.student.action,
      light: WEB_DESIGN.roles.student.tint,
      dark: '#1E3A8A',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: WEB_DESIGN.colors.star,
      light: '#FFFBEB',
      dark: '#D97706',
      contrastText: WEB_DESIGN.colors.ink,
    },
    success: {
      main: WEB_DESIGN.colors.green,
      light: '#ECFDF5',
      dark: '#059669',
      contrastText: '#FFFFFF',
    },
    warning: {
      main: '#F59E0B', // Amber
      light: '#FEF3C7',
      dark: '#B45309',
      contrastText: '#FFFFFF',
    },
    error: {
      main: '#EF4444', // Gentle Red
      light: '#FEE2E2',
      dark: '#DC2626',
      contrastText: '#FFFFFF',
    },
    background: {
      default: WEB_DESIGN.colors.paper,
      paper: WEB_DESIGN.colors.white,
    },
    text: {
      primary: WEB_DESIGN.colors.ink,
      secondary: WEB_DESIGN.colors.mutedInk,
    },
    divider: WEB_DESIGN.colors.line,
  },
  typography: {
    fontFamily: WEB_DESIGN.typography.display,
    h1: {
      fontSize: '2.75rem',
      fontWeight: 900,
      letterSpacing: '-0.025em',
      lineHeight: 1.18,
      color: '#0F172A',
    },
    h2: {
      fontSize: '2.1rem',
      fontWeight: 900,
      letterSpacing: '-0.02em',
      lineHeight: 1.22,
      color: '#0F172A',
    },
    h3: {
      fontSize: '1.6rem',
      fontWeight: 800,
      letterSpacing: '-0.015em',
      lineHeight: 1.28,
      color: '#0F172A',
    },
    h4: {
      fontSize: '1.3rem',
      fontWeight: 800,
      letterSpacing: '-0.01em',
      lineHeight: 1.34,
      color: '#0F172A',
    },
    h5: {
      fontSize: '1.12rem',
      fontWeight: 800,
      letterSpacing: '-0.01em',
      lineHeight: 1.38,
      color: '#0F172A',
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 800,
      lineHeight: 1.4,
      color: '#0F172A',
    },
    subtitle1: {
      fontSize: '0.975rem',
      fontWeight: 700,
      lineHeight: 1.5,
      color: '#475569',
    },
    subtitle2: {
      fontSize: '0.875rem',
      fontWeight: 700,
      lineHeight: 1.5,
      color: '#64748B',
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.65,
      color: '#334155',
    },
    body2: {
      fontSize: '0.9rem',
      lineHeight: 1.58,
      color: '#475569',
    },
    caption: {
      fontSize: '0.8rem',
      lineHeight: 1.5,
      color: '#64748B',
    },
    button: {
      textTransform: 'none',
      fontWeight: 800,
      letterSpacing: '0.01em',
    },
  },
  shape: {
    borderRadius: 14,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#F8FAFC',
          color: '#0F172A',
        },
        '*, *::before, *::after': {
          boxSizing: 'border-box',
        },
        '::selection': {
          backgroundColor: '#DBEAFE',
          color: '#1E40AF',
        },
        ':focus-visible': {
          outline: '3px solid #2563EB',
          outlineOffset: 2,
        },
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
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          borderRadius: 12,
          minHeight: 44,
          padding: '10px 22px',
          fontWeight: 800,
          fontSize: '0.925rem',
          transition: 'all 180ms cubic-bezier(0.16, 1, 0.3, 1)',
          '&:active': {
            transform: 'scale(0.98)',
          },
        },
        contained: {
          backgroundColor: '#2563EB',
          color: '#FFFFFF',
          boxShadow: '0 2px 4px 0 rgba(37, 99, 235, 0.2)',
          '&:hover': {
            backgroundColor: '#1D4ED8',
            boxShadow: '0 6px 16px 0 rgba(37, 99, 235, 0.32)',
            transform: 'translateY(-1px)',
          },
        },
        outlined: {
          borderColor: '#CBD5E1',
          color: '#0F172A',
          backgroundColor: '#FFFFFF',
          boxShadow: '0 1px 2px 0 rgba(15, 23, 42, 0.03)',
          '&:hover': {
            borderColor: '#2563EB',
            backgroundColor: '#EFF6FF',
            color: '#2563EB',
            transform: 'translateY(-1px)',
          },
        },
        sizeSmall: {
          minHeight: 36,
          padding: '6px 16px',
          fontSize: '0.825rem',
          borderRadius: 10,
        },
        sizeLarge: {
          minHeight: 52,
          padding: '14px 28px',
          fontSize: '1.025rem',
          borderRadius: 14,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 18,
          border: '1px solid #E2E8F0',
          boxShadow: '0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 6px 18px -4px rgba(15, 23, 42, 0.04)',
          backgroundImage: 'none',
          backgroundColor: '#FFFFFF',
          transition: 'box-shadow 220ms cubic-bezier(0.16, 1, 0.3, 1), border-color 220ms ease, transform 220ms ease',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
        outlined: {
          borderColor: '#E2E8F0',
          borderRadius: 16,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          fontWeight: 800,
          fontSize: '0.8rem',
          height: 28,
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          backgroundColor: '#FFFFFF',
          fontSize: '0.95rem',
          transition: 'border-color 160ms ease, box-shadow 160ms ease',
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: '#94A3B8',
          },
          '&.Mui-focused': {
            boxShadow: '0 0 0 3px rgba(37, 99, 235, 0.16)',
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: '#2563EB',
            borderWidth: 1.5,
          },
        },
        notchedOutline: {
          borderColor: '#CBD5E1',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: '#F8FAFC',
          '& .MuiTableCell-head': {
            color: '#475569',
            fontWeight: 800,
            fontSize: '0.8125rem',
            letterSpacing: '0.02em',
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
          fontSize: '0.9rem',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: '#F8FAFC !important',
          },
        },
      },
    },
  },
});

export default theme;
