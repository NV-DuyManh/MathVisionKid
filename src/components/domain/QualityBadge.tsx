import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SIZES } from '../../constants/theme';

interface QualityBadgeProps {
  label: string;
  isGood: boolean;
}

export const QualityBadge: React.FC<QualityBadgeProps> = ({ label, isGood }) => {
  return (
    <View style={[styles.container, isGood ? styles.goodContainer : styles.badContainer]}>
      <Ionicons 
        name={isGood ? 'checkmark-circle' : 'alert-circle'} 
        size={16} 
        color={isGood ? COLORS.success : COLORS.warning} 
      />
      <Text style={[styles.text, { color: isGood ? COLORS.success : COLORS.warning }]}>
        {label}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SIZES.small,
    paddingVertical: 4,
    borderRadius: 16,
    borderWidth: 1,
    marginRight: SIZES.small,
    marginBottom: SIZES.small,
  },
  goodContainer: {
    backgroundColor: '#DCFCE7',
    borderColor: '#bbf7d0',
  },
  badContainer: {
    backgroundColor: '#FEF3C7',
    borderColor: '#fde68a',
  },
  text: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  }
});
