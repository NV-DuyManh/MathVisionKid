import { useEffect, useState } from 'react';
import { Box, Typography, Grid, Card, CardContent } from '@mui/material';
import { MockTeacherService } from '../services/api/MockTeacherService';
import type { Class } from '../types';

export default function ClassesPage() {
  const [classes, setClasses] = useState<Class[]>([]);

  useEffect(() => {
    MockTeacherService.getClasses().then(setClasses);
  }, []);

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 4 }}>Danh sách Lớp học</Typography>
      <Grid container spacing={3}>
        {classes.map(c => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={c.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">Lớp {c.name}</Typography>
                <Typography color="text.secondary" sx={{ mt: 1 }}>
                  Sĩ số: {c.studentCount} học sinh
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
