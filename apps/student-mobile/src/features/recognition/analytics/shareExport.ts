import { Alert, Platform, Share } from 'react-native';

export async function shareRecognitionExport(content: string, filename: string) {
  try {
    if (Platform.OS === 'web') {
      const url = URL.createObjectURL(new Blob([content], { type: 'text/plain;charset=utf-8' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } else {
      await Share.share({ title: 'Kết quả nhận dạng MathVision', message: content });
    }
  } catch {
    Alert.alert('Chưa thể xuất kết quả', 'Vui lòng thử lại.');
  }
}
