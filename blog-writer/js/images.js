// Image picker, resize, compress, and blob management

import { saveImage, getImagesForDraft, deleteImage } from './storage.js';

const MAX_DIMENSION = 1600;
const JPEG_QUALITY = 0.8;

function sanitizeFilename(name) {
  return name
    .toLowerCase()
    .replace(/\s+/g, '_')
    .replace(/[^\w.\-]/g, '');
}

export async function pickImage() {
  return new Promise((resolve) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/png,image/jpeg,image/gif';
    input.capture = 'environment';
    input.onchange = async () => {
      if (!input.files || !input.files[0]) {
        resolve(null);
        return;
      }
      const file = input.files[0];
      const processed = await processImage(file);
      resolve(processed);
    };
    input.click();
  });
}

async function processImage(file) {
  // GIFs: don't resize (would lose animation)
  if (file.type === 'image/gif') {
    const buffer = await file.arrayBuffer();
    return {
      name: sanitizeFilename(file.name),
      data: buffer,
      type: 'image/gif',
      base64: arrayBufferToBase64(buffer),
    };
  }

  // Resize and compress
  const bitmap = await createImageBitmap(file);
  let { width, height } = bitmap;

  if (width > MAX_DIMENSION || height > MAX_DIMENSION) {
    if (width > height) {
      height = Math.round(height * MAX_DIMENSION / width);
      width = MAX_DIMENSION;
    } else {
      width = Math.round(width * MAX_DIMENSION / height);
      height = MAX_DIMENSION;
    }
  }

  const canvas = new OffscreenCanvas(width, height);
  const ctx = canvas.getContext('2d');
  ctx.drawImage(bitmap, 0, 0, width, height);
  bitmap.close();

  // Output as JPEG for photos, PNG for things that were PNG
  const isPng = file.type === 'image/png';
  const outputType = isPng ? 'image/png' : 'image/jpeg';
  const quality = isPng ? undefined : JPEG_QUALITY;
  const blob = await canvas.convertToBlob({ type: outputType, quality });
  const buffer = await blob.arrayBuffer();

  let name = sanitizeFilename(file.name);
  if (!isPng && !name.endsWith('.jpg') && !name.endsWith('.jpeg')) {
    name = name.replace(/\.[^.]+$/, '.jpg');
  }

  return {
    name,
    data: buffer,
    type: outputType,
    base64: arrayBufferToBase64(buffer),
  };
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

export async function storeImage(draftId, dateStr, imageData) {
  const id = `${draftId}_${imageData.name}`;
  const record = {
    id,
    draftId,
    dateStr,
    name: imageData.name,
    type: imageData.type,
    base64: imageData.base64,
    data: imageData.data,
  };
  await saveImage(record);
  return record;
}

export async function getStoredImages(draftId) {
  return getImagesForDraft(draftId);
}

export async function removeStoredImage(id) {
  await deleteImage(id);
}

export function createThumbnailUrl(imageRecord) {
  const bytes = new Uint8Array(imageRecord.data);
  const blob = new Blob([bytes], { type: imageRecord.type });
  return URL.createObjectURL(blob);
}

export function markdownImageRef(dateStr, imageName, alt = '') {
  return `![${alt}](files/${dateStr}/${imageName})`;
}
