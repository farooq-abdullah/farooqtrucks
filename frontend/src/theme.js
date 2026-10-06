import { createTheme } from '@mui/material';
export const tokens = {
  paper: '#F4F6F9', raised: '#FFFFFF', ink: '#101F30', ink2: '#475867', ink3: '#5A6B7B',
  rule: '#E2E8F0', ruleStrong: '#788A9B', action: '#244EBA', route: '#244EBA',
  focus: '#244EBA', danger: '#AE3434', subtle: '#EDF2F7', green: '#207557', amber: '#92520C',
};
export const duty = {
  off_duty: { label: 'Off duty', short: 'OFF', color: '#475867' },
  sleeper_berth: { label: 'Sleeper berth', short: 'SB', color: '#4338CA' },
  driving: { label: 'Driving', short: 'D', color: '#244EBA' },
  on_duty: { label: 'On duty', short: 'ON', color: '#207557' },
};
export const DUTY_ORDER = Object.keys(duty);
export const theme = createTheme({
  palette: {
    primary: { main: tokens.action, dark: '#193C95' }, error: { main: tokens.danger },
    success: { main: tokens.green }, warning: { main: tokens.amber },
    background: { default: tokens.paper, paper: tokens.raised },
    text: { primary: tokens.ink, secondary: tokens.ink2 }, divider: tokens.rule,
  },
  shape: { borderRadius: 8 },
  typography: {
    fontFamily: '"IBM Plex Sans", sans-serif', fontSize: 14,
    button: { textTransform: 'none', fontWeight: 500, fontSize: 14 },
    h1: { fontFamily: 'Manrope, sans-serif', fontSize: 32, lineHeight: 1.3125, fontWeight: 700 },
  },
  components: {
    MuiButton: { defaultProps: { disableElevation: true }, styleOverrides: { root: { minHeight: 44, padding: '8px 20px' }, outlined: { borderColor: tokens.ruleStrong } } },
    MuiOutlinedInput: { styleOverrides: { root: { background: '#fff', minHeight: 56, '& fieldset': { borderColor: tokens.ruleStrong } }, input: { padding: '16px', fontSize: 14 } } },
    MuiDialog: { defaultProps: { fullWidth: true, maxWidth: 'sm' } },
    MuiIconButton: { styleOverrides: { root: { minWidth: 44, minHeight: 44 } } },
    MuiTab: { styleOverrides: { root: { minHeight: 44, textTransform: 'none', fontSize: 14, borderRadius: 8, '&.Mui-selected': { background: '#EAF1FB' } } } },
  },
});
