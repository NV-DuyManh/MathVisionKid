import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Alert, Box, CircularProgress } from '@mui/material';
import apiClient from '../../services/api/apiClient';
import { useMocks } from '../../config/runtime';

export function SubmissionImage({ id, mockUrl, studentName }: {
  id: string;
  mockUrl?: string;
  studentName?: string;
}) {
  const image = useQuery({
    queryKey: ['submissionImage', id],
    enabled: !!id && !useMocks,
    queryFn: async ({ signal }) => {
      const response = await apiClient.get<Blob>(`/teacher/submissions/${encodeURIComponent(id)}/image`, {
        responseType: 'blob', signal,
      });
      return response.data;
    },
    staleTime: 60_000,
    retry: false,
  });
  const [loaded, setLoaded] = useState<{ blob: Blob; url: string } | null>(null);

  useEffect(() => {
    if (!image.data) return;
    const url = URL.createObjectURL(image.data);
    // Blob URLs must be allocated and revoked in the effect lifecycle.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoaded({ blob: image.data, url });
    return () => URL.revokeObjectURL(url);
  }, [image.data]);

  const src = useMocks ? mockUrl : loaded && loaded.blob === image.data ? loaded.url : undefined;
  if (image.isError) {
    return <Alert severity="error">Chưa tải được ảnh bài làm. Vui lòng thử mở lại bài.</Alert>;
  }
  if (!src) return <CircularProgress aria-label="Đang tải ảnh bài làm" />;
  return <Box component="img" src={src} alt={`Bài làm của ${studentName || 'học sinh'}`}
    sx={{ maxWidth: '100%', maxHeight: 650, objectFit: 'contain', borderRadius: 1.5 }} />;
}
