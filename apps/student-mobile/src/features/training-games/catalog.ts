import type { TrainingGameId } from '@mathvisionkid/training-games';
import type { Ionicons } from '@expo/vector-icons';
import type { ComponentProps } from 'react';

export const TRAINING_CATALOG: readonly { id: TrainingGameId; title: string; description: string; math: string; icon: ComponentProps<typeof Ionicons>['name']; color: string; tint: string; ready: boolean; note?: string }[] = [
  { id: 'race-to-finish', title: 'Đua Về Đích', description: 'Gieo xúc xắc, giải toán và đua cùng những người bạn.', math: 'Toán lớp 5 · Đếm bước · Tư duy chiến thuật', icon: 'dice-outline', color: '#B25D20', tint: '#FFF1DE', ready: true },
  { id: 'terrain-racing', title: 'Siêu Xe Vượt Địa Hình', description: 'Chọn đúng vận tốc để chinh phục năm chặng đường.', math: 'Quãng đường · Thời gian · Vận tốc', icon: 'car-sport-outline', color: '#286FA8', tint: '#E4F2FF', ready: true },
  { id: 'energy-defense', title: 'Thủ Thành Năng Lượng', description: 'Ghép năng lượng, bảo vệ thành và thử sức ở chế độ Vô Tận.', math: 'Phân số tương đương · Cộng số thập phân', icon: 'shield-checkmark-outline', color: '#257559', tint: '#E3F4E9', ready: true },
  { id: 'planet-rescue', title: 'Giải Cứu Hành Tinh', description: 'Dùng ba thẻ toán để cứu tám hành tinh cùng Nova.', math: 'Rút gọn · Quy đồng · So sánh phân số', icon: 'rocket-outline', color: '#6E51AD', tint: '#EEE7FF', ready: true },
  { id: 'block-island', title: 'Lãnh Chúa Đảo Khối', description: 'Xây thế giới nhiều tầng qua sáu nhiệm vụ nối tiếp.', math: 'Diện tích · Chu vi · Cạnh chung', icon: 'cube-outline', color: '#337B88', tint: '#E0F3F3', ready: true, note: 'Đang tiếp tục hoàn thiện' },
];
