import type { TrainingGameId } from '@mathvisionkid/training-games';
import { GAME_ARTWORK, type GameArtwork } from './GameIcon';
import type { GameMode } from '../student-profile/profileApi';

export const STAR_QUEST = {
  title: 'Đường đua sao',
  description: 'Vượt 5 chặng tính nhẩm để có cơ hội nhận sao vào hồ sơ.',
  artwork: GAME_ARTWORK['star-quest'],
};

export const TRAINING_CATALOG: readonly { id: TrainingGameId; mode: GameMode; title: string; description: string; math: string; grades: readonly [number, number]; artwork: GameArtwork; ready: boolean; note?: string }[] = [
  { id: 'race-to-finish', mode: 'RACE_TO_FINISH', title: 'Đua Về Đích', description: 'Gieo xúc xắc, giải toán và đua cùng những người bạn.', math: 'Toán theo lớp · Đếm bước · Tư duy chiến thuật', grades: [1, 5], artwork: GAME_ARTWORK['race-to-finish'], ready: true },
  { id: 'terrain-racing', mode: 'TERRAIN_RACING', title: 'Siêu Xe Vượt Địa Hình', description: 'Chọn đúng vận tốc để chinh phục năm chặng đường.', math: 'Phép chia theo lớp · Quãng đường · Thời gian', grades: [2, 5], artwork: GAME_ARTWORK['terrain-racing'], ready: true },
  { id: 'energy-defense', mode: 'ENERGY_DEFENSE', title: 'Thủ Thành Năng Lượng', description: 'Ghép năng lượng, bảo vệ thành và thử sức ở chế độ Vô Tận.', math: 'Phép cộng theo lớp · Số tự nhiên · Phân số · Số thập phân', grades: [1, 5], artwork: GAME_ARTWORK['energy-defense'], ready: true },
  { id: 'planet-rescue', mode: 'PLANET_RESCUE', title: 'Giải Cứu Hành Tinh', description: 'Dùng ba thẻ toán để cứu tám hành tinh cùng Nova.', math: 'Rút gọn · Quy đồng · So sánh phân số', grades: [4, 5], artwork: GAME_ARTWORK['planet-rescue'], ready: true },
  { id: 'block-island', mode: 'BLOCK_ISLAND', title: 'Lãnh Chúa Đảo Khối', description: 'Xây thế giới nhiều tầng qua sáu nhiệm vụ nối tiếp.', math: 'Diện tích · Chu vi · Cạnh chung', grades: [3, 5], artwork: GAME_ARTWORK['block-island'], ready: true, note: 'Đang tiếp tục hoàn thiện' },
];
