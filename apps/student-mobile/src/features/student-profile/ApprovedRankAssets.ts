import type { ImageSourcePropType } from 'react-native';

export const approvedRanks = [
  { id: 'dong', name: 'Đồng', source: require('../../../assets/rank-tutien-transparent/normalized/01_dong.png') as ImageSourcePropType },
  { id: 'bac', name: 'Bạc', source: require('../../../assets/rank-tutien-transparent/normalized/02_bac.png') as ImageSourcePropType },
  { id: 'vang', name: 'Vàng', source: require('../../../assets/rank-tutien-transparent/normalized/03_vang.png') as ImageSourcePropType },
  { id: 'bach-kim', name: 'Bạch Kim', source: require('../../../assets/rank-tutien-transparent/rank/04_bach-kim.png') as ImageSourcePropType },
  { id: 'kim-cuong', name: 'Kim Cương', source: require('../../../assets/rank-tutien-transparent/rank/05_kim-cuong.png') as ImageSourcePropType },
  { id: 'cao-thu', name: 'Cao Thủ', source: require('../../../assets/rank-tutien-transparent/rank/06_cao-thu.png') as ImageSourcePropType },
  { id: 'dai-cao-thu', name: 'Đại Cao Thủ', source: require('../../../assets/rank-tutien-transparent/rank/07_dai-cao-thu.png') as ImageSourcePropType },
  { id: 'thach-dau', name: 'Thách Đấu', source: require('../../../assets/rank-tutien-transparent/rank/08_thach-dau.png') as ImageSourcePropType },
  { id: 'huyen-thoai', name: 'Huyền Thoại', source: require('../../../assets/rank-tutien-transparent/rank/09_huyen-thoai.png') as ImageSourcePropType },
] as const;
export function approvedRankAsset(name: string) {
  const tier = name.replace(/ [IV]+$/, '');
  const canonical = tier === 'Tinh Anh' ? 'Cao Thủ' : tier === 'Chiến Tướng' || tier === 'Chiến Thần' ? 'Thách Đấu' : tier;
  return approvedRanks.find(item => item.name === canonical)?.source;
}
