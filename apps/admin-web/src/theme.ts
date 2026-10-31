import { createTheme } from '@mui/material/styles';
export const adminTheme = createTheme({
  palette: {
    primary: { main: '#7055F6', dark: '#5637C9', light: '#EDE9FF', contrastText: '#fff' },
    background: { default: '#F8F7FE', paper: '#fff' },
    text: { primary: '#18164C', secondary: '#625B79' }, divider: '#E8E5EF',
    success: { main: '#207553', light: '#EAF6F0' },
    error: { main: '#B63245', light: '#FCEEF0' }, warning: { main: '#8B600C', light: '#FFF7E5' },
  },
  typography: {
    fontFamily: 'Nunito, "Segoe UI", sans-serif',
    h1: { fontSize: '2rem', fontWeight: 800 }, h2: { fontSize: '1.75rem', fontWeight: 800 },
    h3: { fontSize: '1.5rem', fontWeight: 800 }, h4: { fontSize: '1.8rem', fontWeight: 800, letterSpacing: '-.035em' },
    h5: { fontSize: '1.35rem', fontWeight: 800 }, h6: { fontSize: '1.05rem', fontWeight: 800 },
    body1: { fontSize: '.95rem', lineHeight: 1.65 }, body2: { fontSize: '.875rem', lineHeight: 1.6 },
    caption: { fontSize: '.77rem', lineHeight: 1.6 }, button: { textTransform: 'none', fontWeight: 800 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiCssBaseline: { styleOverrides: {
      '*, *::before, *::after': { boxSizing: 'border-box' },
      ':focus-visible': { outline: '3px solid #9271D0', outlineOffset: 3 },
      '@media (prefers-reduced-motion: reduce)': { '*, *::before, *::after': { animationDuration: '.01ms !important', transitionDuration: '.01ms !important', scrollBehavior: 'auto !important' } },
    } },
    MuiButton: { defaultProps: { disableElevation: true }, styleOverrides: { root: { minHeight: 44, borderRadius: 12, padding: '9px 17px' }, sizeSmall: { minHeight: 38 } } },
    MuiIconButton: { styleOverrides: { root: { minHeight: 44, minWidth: 44 } } },
    MuiCardContent: { styleOverrides: { root: { padding: 24, '&:last-child': { paddingBottom: 24 } } } },
    MuiCard: { styleOverrides: { root: { borderRadius: 22, border: '1px solid #EAE6F5', boxShadow: '0 6px 24px #30205D05', backgroundImage: 'none', minWidth: 0 } } },
    MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
    MuiChip: { styleOverrides: { root: { borderRadius: 8, fontWeight: 800, fontSize: '.73rem' } } },
    MuiTableContainer: { styleOverrides: { root: { maxWidth: '100%', overflowX: 'auto' } } },
    MuiTableCell: { styleOverrides: { root: { padding: '16px 20px', borderColor: '#EFEDF4', fontSize: '.85rem' }, head: { color: '#625775', fontWeight: 800, backgroundColor: '#FAF9FC', whiteSpace: 'nowrap' } } },
    MuiTableRow: { styleOverrides: { root: { '&.MuiTableRow-hover:hover': { backgroundColor: '#FBF9FF' } } } },
    MuiTablePagination: { defaultProps: {
      labelRowsPerPage: 'Số dòng:',
      labelDisplayedRows: ({ from, to, count }) => `${from}–${to} / ${count}`,
    } },
    MuiOutlinedInput: { styleOverrides: { root: { borderRadius: 10, backgroundColor: '#fff' } } },
    MuiDialog: { styleOverrides: { paper: { borderRadius: 24 } } },
    MuiDialogTitle: { styleOverrides: { root: { fontWeight: 800 } } },
    MuiAlert: { styleOverrides: { root: { borderRadius: 10 } } },
  },
});
