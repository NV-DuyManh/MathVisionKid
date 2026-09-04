import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { COLORS, SIZES } from '../../constants/theme';
import { AppCard } from '../ui/AppCard';
import { AppButton } from '../ui/AppButton';

interface TokenConfirmationCardProps {
  initialToken: string;
  onConfirm: (token: string) => void;
}

export const TokenConfirmationCard: React.FC<TokenConfirmationCardProps> = ({ initialToken, onConfirm }) => {
  const [token, setToken] = useState(initialToken);
  const [isEditing, setIsEditing] = useState(false);

  const digits = ['1','2','3','4','5','6','7','8','9','0'];

  return (
    <AppCard style={styles.container}>
      <Text style={styles.title}>MathVision nghĩ em viết:</Text>
      
      <View style={styles.tokenBox}>
        <Text style={styles.tokenText}>{token}</Text>
      </View>

      {!isEditing ? (
        <View style={styles.actionRow}>
          <AppButton 
            title="Sửa" 
            onPress={() => setIsEditing(true)} 
            variant="outlined"
            style={styles.halfButton} 
          />
          <View style={{ width: SIZES.medium }} />
          <AppButton 
            title="Đúng" 
            onPress={() => onConfirm(token)} 
            style={styles.halfButton} 
          />
        </View>
      ) : (
        <View style={styles.keypad}>
          <Text style={styles.instruction}>Chọn số đúng:</Text>
          <View style={styles.grid}>
            {digits.map(d => (
              <TouchableOpacity 
                key={d} 
                style={styles.digitButton}
                onPress={() => {
                  setToken(d);
                  setIsEditing(false);
                }}
              >
                <Text style={styles.digitButtonText}>{d}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}
    </AppCard>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    paddingVertical: SIZES.large,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: SIZES.medium,
  },
  tokenBox: {
    width: 80,
    height: 100,
    borderWidth: 2,
    borderColor: COLORS.primary,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#EEF2FF',
    marginBottom: SIZES.large,
  },
  tokenText: {
    fontSize: 48,
    fontWeight: 'bold',
    color: COLORS.primaryDark,
  },
  actionRow: {
    flexDirection: 'row',
    width: '100%',
    justifyContent: 'space-between',
  },
  halfButton: {
    flex: 1,
  },
  keypad: {
    width: '100%',
    alignItems: 'center',
  },
  instruction: {
    fontSize: 16,
    color: COLORS.textSecondary,
    marginBottom: SIZES.medium,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: SIZES.small,
  },
  digitButton: {
    width: 60,
    height: 60,
    backgroundColor: COLORS.background,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  digitButtonText: {
    fontSize: 24,
    fontWeight: '600',
    color: COLORS.textPrimary,
  }
});
