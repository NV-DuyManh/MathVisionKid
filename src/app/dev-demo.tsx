import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS, SIZES } from '../constants/theme';
import { AppHeader } from '../components/ui/AppHeader';

export default function DevDemoScreen() {
  const router = useRouter();

  const handleMock = (mockName: string) => {
    router.push({ pathname: '/preview', params: { uri: `file://${mockName}.jpg` } });
  };

  return (
    <View style={styles.container}>
      <AppHeader title="QA Demo Mocks" showBack />
      
      <ScrollView style={styles.content}>
        <Text style={styles.instruction}>Chỉ dành cho QA/Developer test luồng UI.</Text>
        
        <View style={styles.grid}>
          {[
            { label: 'Correct (Flow A)', key: 'mock-correct' },
            { label: 'Earliest Error (Flow B)', key: 'mock-earliest-error' },
            { label: 'Needs Confirmation (Flow C)', key: 'mock-confirm' },
            { label: 'Needs Retake (Flow D)', key: 'mock-blur' },
            { label: 'Crop Required', key: 'mock-crop' },
            { label: 'Out of Scope (Flow E)', key: 'mock-out-of-scope' },
            { label: 'Review Required (Flow F)', key: 'mock-review' },
          ].map(mock => (
            <TouchableOpacity 
              key={mock.key}
              style={styles.demoPill}
              onPress={() => handleMock(mock.key)}
            >
              <Text style={styles.demoPillText}>{mock.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    padding: SIZES.medium,
  },
  instruction: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: SIZES.large,
    textAlign: 'center',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  demoPill: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: SIZES.cardRadius,
    width: '100%',
  },
  demoPillText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.surface,
    textAlign: 'center',
  }
});
