const colors = {
  ink: '#172554',
  mutedInk: '#475569',
  paper: '#FFFBF0',
  white: '#FFFFFF',
  line: '#DCE3EF',
  paperLine: '#E2D8BA',
  blue: '#1D4ED8',
  blueLight: '#EAF2FF',
  green: '#047857',
  greenLight: '#E9F7F0',
  indigo: '#4338CA',
  indigoLight: '#EEEDFF',
  star: '#F6C34E',
} as const;

const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32 } as const;
const radii = { control: 12, panel: 12, notebook: 20 } as const;

export const WEB_DESIGN = {
  colors,
  roles: {
    student: { action: colors.blue, tint: colors.blueLight },
    teacher: { action: colors.green, tint: colors.greenLight },
    admin: { action: colors.indigo, tint: colors.indigoLight },
  },
  space,
  radii,
  typography: {
    display: '"Nunito", "Plus Jakarta Sans", "Segoe UI", sans-serif',
    body: '"Plus Jakarta Sans", Inter, "Segoe UI", sans-serif',
    sizes: { caption: 14, body: 16, section: 20, heading: 28, display: 40 },
  },
  motion: { press: 120, panel: 180 },
  focus: { color: colors.blue, width: 3, offset: 3 },
  components: {
    action: { minHeight: 44, radius: radii.control },
    workspacePanel: { radius: radii.panel, borderColor: colors.line },
    notebook: { radius: radii.notebook, borderColor: colors.paperLine },
  },
} as const;
