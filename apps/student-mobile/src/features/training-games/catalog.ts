import type { TrainingGameId } from '@mathvisionkid/training-games';
import type { GameArtwork } from './GameIcon';
import type { GameMode } from '../student-profile/profileApi';

export const STAR_QUEST = {
  title: 'Đường đua sao',
  description: 'Vượt 5 chặng tính nhẩm để có cơ hội nhận sao vào hồ sơ.',
  artwork: { icon: 'star', accent: 'flash', color: '#9A4D0D', tint: '#FFF0C7' } satisfies GameArtwork,
};

export const TRAINING_CATALOG: readonly { id: TrainingGameId; mode: GameMode; title: string; description: string; math: string; artwork: GameArtwork; ready: boolean; note?: string }[] = [
  { id: 'race-to-finish', mode: 'RACE_TO_FINISH', title: 'Đua Về Đích', description: 'Gieo xúc xắc, giải toán và đua cùng những người bạn.', math: 'Toán lớp 5 · Đếm bước · Tư duy chiến thuật', artwork: { icon: 'dice', accent: 'flag', color: '#AC4F25', tint: '#FFEADA' }, ready: true },
  { id: 'terrain-racing', mode: 'TERRAIN_RACING', title: 'Siêu Xe Vượt Địa Hình', description: 'Chọn đúng vận tốc để chinh phục năm chặng đường.', math: 'Quãng đường · Thời gian · Vận tốc', artwork: { icon: 'car-sport', accent: 'speedometer', color: '#22649D', tint: '#E4F2FF' }, ready: true },
  { id: 'energy-defense', mode: 'ENERGY_DEFENSE', title: 'Thủ Thành Năng Lượng', description: 'Ghép năng lượng, bảo vệ thành và thử sức ở chế độ Vô Tận.', math: 'Phân số tương đương · Cộng số thập phân', artwork: { icon: 'shield', accent: 'flash', color: '#20654C', tint: '#DFF5E7' }, ready: true },
  { id: 'planet-rescue', mode: 'PLANET_RESCUE', title: 'Giải Cứu Hành Tinh', description: 'Dùng ba thẻ toán để cứu tám hành tinh cùng Nova.', math: 'Rút gọn · Quy đồng · So sánh phân số', artwork: { icon: 'rocket', accent: 'planet', color: '#623CA3', tint: '#EEE7FF' }, ready: true },
  { id: 'block-island', mode: 'BLOCK_ISLAND', title: 'Lãnh Chúa Đảo Khối', description: 'Xây thế giới nhiều tầng qua sáu nhiệm vụ nối tiếp.', math: 'Diện tích · Chu vi · Cạnh chung', artwork: { icon: 'cube', accent: 'grid', color: '#236773', tint: '#DBF1F3' }, ready: true, note: 'Đang tiếp tục hoàn thiện' },
];
