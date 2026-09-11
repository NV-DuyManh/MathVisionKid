import * as ImageManipulator from 'expo-image-manipulator';
import { ImageDraft } from '../draft/submissionDraftStore';

export function ensureFileUri(uri: string): string {
  if (!uri || typeof uri !== 'string') return '';
  if (uri.startsWith('file://') || uri.startsWith('content://') || uri.startsWith('http://') || uri.startsWith('https://')) {
    return uri;
  }
  return `file://${uri}`;
}

export function logStageDiagnostic(
  stage:
    | 'ACQUIRE_CAMERA'
    | 'ACQUIRE_GALLERY'
    | 'NORMALIZED'
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

export async function normalizeImageDraft(
  inputUri: string,
  knownWidth?: number,
  knownHeight?: number,
  source?: 'CAMERA' | 'GALLERY'
): Promise<ImageDraft> {
  const cleanUri = Array.isArray(inputUri) ? inputUri[0] : inputUri;
  if (!cleanUri || typeof cleanUri !== 'string') {
    throw new Error('INVALID_IMAGE_URI: Provided URI is empty or not a valid string.');
  }

  // Ensure URI has proper scheme before manipulation
  const preparedUri = ensureFileUri(cleanUri);

  try {
    // Materialize into a stable, non-transient JPEG file in app cache and normalize EXIF orientation
    const manipResult = await ImageManipulator.manipulateAsync(
      preparedUri,
      [], // no transformations; this acts as a materialize & orientation pass
      { compress: 0.95, format: ImageManipulator.SaveFormat.JPEG }
    );

    const stableUri = ensureFileUri(manipResult.uri);
    const resolvedWidth = manipResult.width || knownWidth || 0;
    const resolvedHeight = manipResult.height || knownHeight || 0;

    const filename = `mathvision_${Date.now()}.jpg`;

    const draft: ImageDraft = {
      rawUri: cleanUri,
      uri: stableUri,
      width: resolvedWidth,
      height: resolvedHeight,
      mimeType: 'image/jpeg',
      filename,
      source: source || 'CAMERA',
      isMasked: false,
    };

    logStageDiagnostic('NORMALIZED', {
      uri: stableUri,
      width: resolvedWidth,
      height: resolvedHeight,
      mimeType: 'image/jpeg',
      source: draft.source,
    });

    return draft;
  } catch (err) {
    console.warn('[IMAGE_PIPELINE] manipulateAsync fallback used:', err);
    // If manipulateAsync throws (e.g. on web or unsupported mock), fall back gracefully
    const stableUri = ensureFileUri(cleanUri);
    const draft: ImageDraft = {
      rawUri: cleanUri,
      uri: stableUri,
      width: knownWidth || 0,
      height: knownHeight || 0,
      mimeType: 'image/jpeg',
      filename: `mathvision_${Date.now()}.jpg`,
      source: source || 'CAMERA',
      isMasked: false,
    };

    logStageDiagnostic('NORMALIZED', {
      uri: stableUri,
      width: draft.width,
      height: draft.height,
      mimeType: 'image/jpeg',
      source: draft.source,
      extra: 'fallback',
    });

    return draft;
  }
}
