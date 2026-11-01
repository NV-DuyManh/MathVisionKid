import { Box, type BoxProps } from '@mui/material';
export function PageContent(props: BoxProps) {
  return <Box {...props} className="workspace-content" sx={{ p: { xs: 2, sm: 3, lg: 4 }, ...props.sx }} />;
}
