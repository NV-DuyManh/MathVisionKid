import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#2563EB',      // MathVision Royal Blue
      dark: '#1D4ED8',
      light: '#DBEAFE',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#0D9488',      // Education Teal
      dark: '#0F766E',
      light: '#CCFBF1',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#F8FAFC',   // Slate 50
      paper: '#FFFFFF',
    },
    text: {
      primary: '#0F172A',   // Slate 900
      secondary: '#475569', // Slate 600
    },
    error: {
      main: '#DC2626',      // Red 600
      dark: '#B91C1C',      // Red 700
      light: '#FEF2F2',     // Red 50
      contrastText: '#FFFFFF',
    },
    success: {
      main: '#16A34A',      // Green 600
      dark: '#15803D',      // Green 700
      light: '#DCFCE7',     // Green 100
      contrastText: '#FFFFFF',
    },
    warning: {
      main: '#D97706',      // Amber 600
      dark: '#B45309',      // Amber 700
      light: '#FEF3C7',     // Amber 100
      contrastText: '#FFFFFF',
    },
    info: {
      main: '#2563EB',
      dark: '#1D4ED8',
      light: '#EFF6FF',
      contrastText: '#FFFFFF',
    },
    divider: '#E2E8F0',     // Slate 200
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 800,
      letterSpacing: '-0.02em',
      color: '#0F172A',
    },
    h5: {
      fontWeight: 700,
      letterSpacing: '-0.01em',
      color: '#0F172A',
    },
    h6: {
      fontWeight: 700,
      letterSpacing: '-0.005em',
      color: '#0F172A',
    },
    subtitle1: {
      fontWeight: 600,
      color: '#0F172A',
    },
    subtitle2: {
      fontWeight: 600,
      color: '#475569',
    },
    body1: {
      color: '#0F172A',
      fontSize: '0.9375rem',
      lineHeight: 1.5,
    },
    body2: {
      color: '#475569',
      fontSize: '0.875rem',
      lineHeight: 1.45,
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
      letterSpacing: '0.01em',
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: `
        @media (prefers-reduced-motion: reduce) {
          * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
          }
        }
        body {
          background-color: #F8FAFC;
        }
      `,
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: 'none',
          padding: '8px 16px',
          fontWeight: 600,
          transition: 'all 150ms ease-in-out',
          '&:hover': {
            boxShadow: '0 2px 4px -1px rgba(0, 0, 0, 0.06), 0 1px 2px -1px rgba(0, 0, 0, 0.04)',
          },
          '&.MuiButton-containedPrimary': {
            backgroundColor: '#2563EB',
            '&:hover': {
              backgroundColor: '#1D4ED8',
            },
          },
          '&:focus-visible': {
            outline: '2px solid #2563EB',
            outlineOffset: '2px',
          },
        },
        sizeLarge: {
          padding: '10px 22px',
          fontSize: '0.95rem',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px 0 rgba(15, 23, 42, 0.06), 0 1px 2px -1px rgba(15, 23, 42, 0.04)',
          border: '1px solid #E2E8F0',
          borderRadius: 10,
          transition: 'box-shadow 150ms ease-in-out, border-color 150ms ease-in-out',
          '&:hover': {
            boxShadow: '0 4px 6px -1px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.06)',
          },
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
          borderRadius: 10,
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: '#F8FAFC',
          '& .MuiTableCell-head': {
            fontWeight: 700,
            fontSize: '0.8125rem',
            color: '#475569',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            borderBottom: '1px solid #E2E8F0',
            padding: '12px 16px',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid #F1F5F9',
          padding: '12px 16px',
          fontSize: '0.875rem',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: '#F8FAFC',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          borderRadius: 6,
          height: 26,
          fontSize: '0.8125rem',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            '&:hover fieldset': {
              borderColor: '#94A3B8',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#2563EB',
              borderWidth: 2,
            },
          },
        },
      },
    },
  },
});
