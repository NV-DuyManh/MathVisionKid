import * as ImageManipulator from 'expo-image-manipulator';
import * as FileSystem from 'expo-file-system/legacy';
import { Image, Platform } from 'react-native';
import { ImageDraft } from '../state/recognitionDraftStore';
import { exportCropImage } from '../../../utils/cropRotation';

/**
 * Normalizes local file URIs safely.
 * - Adds file:// only to local paths; preserves browser and content URIs
 * - NEVER runs decodeURIComponent() or decodeURI() on file:// paths
 * - Preserves literal percent-encoded Expo ExperienceData paths (%2540 / %40)
 */
export function normalizeLocalFileUri(uri: string): string {
  if (!uri || typeof uri !== 'string') return '';
  let clean = uri.trim();
  if (
    !clean.startsWith('ph://') &&
    !clean.startsWith('assets-library://') &&
    !clean.startsWith('file://') &&
    !clean.startsWith('content://') &&
    !clean.startsWith('blob:') &&
    !clean.startsWith('data:') &&
    !clean.startsWith('http://') &&
    !clean.startsWith('https://')
  ) {
    clean = clean.startsWith('/') ? `file://${clean}` : `file:///${clean}`;
  }
  // Keep file:// URI unchanged — never decode existing Expo cache / ExperienceData URI
  return clean;
}

export const normalizeFileUri = normalizeLocalFileUri;
export const ensureFileUri = normalizeLocalFileUri;

/**
 * Validates local file existence via FileSystem.getInfoAsync and copies to cache directory if missing.
 * Logs [CROP_DEBUG] diagnostic details.
 */
export async function resolveSafeCropImage(
  inputUri: string,
  candidateFallbacks: (string | undefined)[] = []
): Promise<{
  originalUri: string;
  normalizedUri: string;
  exists: boolean;
  finalUri: string;
}> {
  const originalUri = inputUri || '';
  const normalizedUri = normalizeLocalFileUri(originalUri);

  // On Web or if empty URI, bypass native FileSystem checks
  if (Platform.OS === 'web' || !normalizedUri) {
    const exists = !!normalizedUri;
    const finalUri = normalizedUri;
    console.log(
      `[CROP_DEBUG]\noriginalUri=${originalUri}\nnormalizedUri=${normalizedUri}\nexists=${exists}\nfinalUri=${finalUri}`
    );
    return { originalUri, normalizedUri, exists, finalUri };
  }

  // 1. Check primary normalized URI
  let exists = false;
  try {
    const info = await FileSystem.getInfoAsync(normalizedUri);
    exists = !!info.exists;
  } catch {
    exists = false;
  }

  if (exists) {
    const finalUri = normalizedUri;
    console.log(
      `[CROP_DEBUG]\noriginalUri=${originalUri}\nnormalizedUri=${normalizedUri}\nexists=${exists}\nfinalUri=${finalUri}`
    );
    return { originalUri, normalizedUri, exists, finalUri };
  }

  // 2. If primary doesn't exist, test candidate alternatives and path variations
  const pool = new Set<string>();
  candidateFallbacks.forEach((u) => {
    if (u && typeof u === 'string') pool.add(normalizeLocalFileUri(u));
  });

  const addVariations = (base: string) => {
    if (!base) return;
    // Android Expo Go ExperienceData variations
    if (base.includes('@anonymous')) {
      pool.add(base.replace(/@anonymous(?:\/[^/]+)?/g, (experience) => encodeURIComponent(experience)));
      pool.add(base.replace(/@anonymous(?:\/[^/]+)?/g, (experience) => encodeURIComponent(encodeURIComponent(experience))));
    }
    if (base.includes('%40')) {
      pool.add(base.replace(/%40/g, '%2540').replace(/%2F/g, '%252F'));
      pool.add(base.replace(/%40/g, '@'));
    }
    if (base.includes('%2540')) {
      pool.add(base.replace(/%2540/g, '%40').replace(/%252F/g, '%2F'));
      pool.add(base.replace(/%2540/g, '@'));
    }
  };

  addVariations(normalizedUri);
  candidateFallbacks.forEach((u) => u && addVariations(u));

  let workingSourceUri: string | null = null;
  for (const candidate of pool) {
    if (!candidate || candidate === normalizedUri) continue;
    try {
      const info = await FileSystem.getInfoAsync(candidate);
      if (info.exists) {
        workingSourceUri = candidate;
        break;
      }
    } catch {
      // continue scanning
    }
  }

  // 3. If image path does not exist (or alternate source was found), copy to FileSystem.cacheDirectory
  let finalUri = normalizedUri;
  const sourceToCopy = workingSourceUri || (normalizedUri.startsWith('content://') ? normalizedUri : null);

  if (sourceToCopy) {
    try {
      const destFilename = `recognition_crop_${Date.now()}.jpg`;
      const cacheDir = FileSystem.cacheDirectory || '';
      const destUri = `${cacheDir}${destFilename}`;
      await FileSystem.copyAsync({ from: sourceToCopy, to: destUri });
      const verify = await FileSystem.getInfoAsync(destUri);
      if (verify.exists) {
        exists = true;
        finalUri = destUri;
      }
    } catch (copyErr) {
      console.warn('[CROP_DEBUG] Failed to copy image to cacheDirectory:', copyErr);
      if (workingSourceUri) {
        exists = true;
        finalUri = workingSourceUri;
      }
    }
  }

  console.log(
    `[CROP_DEBUG]\noriginalUri=${originalUri}\nnormalizedUri=${normalizedUri}\nexists=${exists}\nfinalUri=${finalUri}`
  );
  return { originalUri, normalizedUri, exists, finalUri };
}

export function logStageDiagnostic(
  stage:
    | 'ACQUIRE_CAMERA'
    | 'ACQUIRE_GALLERY'
    | 'NORMALIZED'
    | 'IMAGE_READABLE'
    | 'IMAGE_READ_ERROR'
    | 'PRIVACY_LOAD_START'
    | 'PRIVACY_LOAD_SUCCESS'
    | 'PRIVACY_LOAD_ERROR'
    | 'PRIVACY_INPUT'
    | 'PRIVACY_OUTPUT'
    | 'PREVIEW_INPUT'
    | 'CROP_INPUT'
    | 'CROP_OUTPUT'
    | 'PROCESSING_INPUT'
    | 'MULTIPART_READY'
    | 'UPLOAD_RESPONSE'
    | 'TERMINAL_STATUS',
  meta: {
    uri?: string;
    width?: number;
    height?: number;
    mimeType?: string;
    source?: 'CAMERA' | 'GALLERY' | string;
    extra?: string;
  }
): void {
  const scheme = meta.uri ? (meta.uri.match(/^(\w+):\/\//) || ['unknown:'])[0] : 'none';
  const tail = meta.uri ? meta.uri.split('/').pop()?.split('?')[0] : 'none';
  console.log(
    `[DEV_STAGE][${stage}] scheme=${scheme} file=${tail} WxH=${meta.width ?? '?' }x${meta.height ?? '?'} mime=${meta.mimeType || 'n/a'} src=${meta.source || 'n/a'} ${meta.extra ? `(${meta.extra})` : ''}`
  );
}


export interface ReadableImage {
  uri: string;
  width: number;
  height: number;
}

/** Check the actual file and decoder, never trust picker dimensions or an old cache URI. */
export function inspectReadableImage(inputUri: string): Promise<ReadableImage> {
  const uri = ensureFileUri(inputUri);
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (image?: ReadableImage, error?: Error) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      if (image) {
        logStageDiagnostic('IMAGE_READABLE', image);
        resolve(image);
      } else {
        logStageDiagnostic('IMAGE_READ_ERROR', { uri, extra: error?.message });
        reject(error);
      }
    };
    // A deadline is a failure, never evidence that an image has loaded.
    const timer = setTimeout(() => finish(undefined, new Error('IMAGE_READ_TIMEOUT')), 10000);
    void (async () => {
      if (!uri) throw new Error('INVALID_IMAGE_URI');
      if (Platform.OS !== 'web' && uri.startsWith('file://')) {
        const info = await FileSystem.getInfoAsync(uri);
        if (!info.exists || info.isDirectory || info.size === 0) throw new Error('IMAGE_FILE_MISSING');
      }
      if (settled) return;
      Image.getSize(uri, (width, height) => {
        if (Number.isFinite(width) && Number.isFinite(height) && width > 0 && height > 0) {
          finish({ uri, width, height });
        } else {
          finish(undefined, new Error('IMAGE_INVALID_DIMENSIONS'));
        }
      }, () => finish(undefined, new Error('IMAGE_DECODE_FAILED')));
    })().catch(() => finish(undefined, new Error('IMAGE_FILE_UNREADABLE')));
  });
}

export async function normalizeImageDraft(
  inputUri: string,
  _knownWidth?: number,
  _knownHeight?: number,
  source?: 'CAMERA' | 'GALLERY'
): Promise<ImageDraft> {
  const cleanUri = Array.isArray(inputUri) ? inputUri[0] : inputUri;
  if (!cleanUri || typeof cleanUri !== 'string') throw new Error('INVALID_IMAGE_URI');
  const preparedUri = ensureFileUri(cleanUri);
  // Conversion must succeed. Returning an unverified HEIC/asset URI labelled JPEG is unsafe.
  const manipResult = Platform.OS === 'web'
    ? await exportCropImage(preparedUri, 0, { x: 0, y: 0, w: 1, h: 1 })
    : await ImageManipulator.manipulateAsync(preparedUri, [], {
      compress: 0.95, format: ImageManipulator.SaveFormat.JPEG,
    });
  const stableUri = ensureFileUri(manipResult.uri);
  if (Platform.OS !== 'web' && !stableUri.startsWith('file://')) throw new Error('IMAGE_NOT_MATERIALIZED');
  const image = await inspectReadableImage(stableUri);
  const draft: ImageDraft = {
    imageSessionId: `session_${Date.now()}_${Math.random().toString(36).slice(2)}`,
    originalImageUri: stableUri,
    originalUri: stableUri,
    sourceImageUri: stableUri,
    rawUri: cleanUri,
    uri: stableUri,
    width: image.width,
    height: image.height,
    mimeType: 'image/jpeg',
    filename: `mathvision_${Date.now()}.jpg`,
    source: source || 'CAMERA',
    isMasked: false,
    privacyConfirmed: false,
  };
  logStageDiagnostic('NORMALIZED', { ...image, mimeType: draft.mimeType, source: draft.source });
  return draft;
}
