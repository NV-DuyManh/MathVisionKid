/** Shared MathVision identity. OCR and arithmetic are native features. */
export function getAppBranding() {
  return {
    name: 'MathVision Kids',
    subtitle: 'Cùng em nhận diện và rèn luyện chữ viết tay mỗi ngày',
    detailedSubtitle: 'Trợ lý toán học cho học sinh tiểu học',
    tagline: 'Chụp bài • Hiểu lỗi • Tự sửa',
    badgeText: 'MATHVISION KIDS',
    features: ['Chụp và nhận diện bài làm', 'Phát hiện dòng và phép tính', 'Chỉ ra lỗi sai từng bước', 'Gợi ý tự sửa bài tập'],
    featuresVi: ['Chụp và nhận diện bài làm', 'Phát hiện dòng và phép tính', 'Chỉ ra lỗi sai từng bước', 'Gợi ý tự sửa bài tập'],
  };
}

export function getFeatureFlags() {
  return {
    showMathCalculations: true, showArithmeticMode: true,
    showHandwritingPipeline: true, showPrivacyProtection: true,
    showExerciseHistory: true, showCaptureTips: true,
  };
}
