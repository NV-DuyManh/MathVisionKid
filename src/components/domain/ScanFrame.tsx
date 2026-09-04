import React from 'react';
import { View, StyleSheet, Dimensions, Text } from 'react-native';
import { COLORS } from '../../constants/theme';

export function ScanFrame() {
  return (
    <View style={styles.container} pointerEvents="none">
      <View style={styles.overlay}>
        <View style={styles.topMask} />
        <View style={styles.centerRow}>
          <View style={styles.sideMask} />
          <View style={styles.frame}>
            {/* Corner Markers */}
            <View style={[styles.corner, styles.topLeft]} />
            <View style={[styles.corner, styles.topRight]} />
            <View style={[styles.corner, styles.bottomLeft]} />
            <View style={[styles.corner, styles.bottomRight]} />
            
            <View style={styles.textContainer}>
              <Text style={styles.instruction}>Đặt toàn bộ phép tính vào khung</Text>
            </View>
          </View>
          <View style={styles.sideMask} />
        </View>
        <View style={styles.bottomMask}>
          <Text style={styles.secondaryInstruction}>Chỉ chụp một bài mỗi lần</Text>
        </View>
      </View>
    </View>
  );
}

const { width } = Dimensions.get('window');
// Frame takes ~80% of width
const frameWidth = width * 0.8;
const frameHeight = frameWidth * 1.2; // slight vertical rectangle
const cornerLength = 40;
const cornerWidth = 5;
const cornerColor = COLORS.surface;

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFill,
    zIndex: 10,
  },
  overlay: {
    flex: 1,
  },
  topMask: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  centerRow: {
    flexDirection: 'row',
    height: frameHeight,
  },
  sideMask: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  frame: {
    width: frameWidth,
    backgroundColor: 'transparent',
    justifyContent: 'flex-end',
    alignItems: 'center',
    paddingBottom: 24,
  },
  bottomMask: {
    flex: 1.2,
    backgroundColor: 'rgba(0,0,0,0.5)',
    alignItems: 'center',
    paddingTop: 24,
  },
  corner: {
    position: 'absolute',
    borderColor: cornerColor,
  },
  topLeft: {
    top: 0, left: 0,
    width: cornerLength, height: cornerLength,
    borderTopWidth: cornerWidth, borderLeftWidth: cornerWidth,
    borderTopLeftRadius: 16,
  },
  topRight: {
    top: 0, right: 0,
    width: cornerLength, height: cornerLength,
    borderTopWidth: cornerWidth, borderRightWidth: cornerWidth,
    borderTopRightRadius: 16,
  },
  bottomLeft: {
    bottom: 0, left: 0,
    width: cornerLength, height: cornerLength,
    borderBottomWidth: cornerWidth, borderLeftWidth: cornerWidth,
    borderBottomLeftRadius: 16,
  },
  bottomRight: {
    bottom: 0, right: 0,
    width: cornerLength, height: cornerLength,
    borderBottomWidth: cornerWidth, borderRightWidth: cornerWidth,
    borderBottomRightRadius: 16,
  },
  textContainer: {
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  instruction: {
    color: COLORS.surface,
    fontSize: 14,
    fontWeight: '600',
  },
  secondaryInstruction: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 14,
  }
});
