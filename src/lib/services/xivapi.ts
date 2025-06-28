import { base } from "$app/paths";

export const XIVAPI_BETA_BASE_URL = "https://beta.xivapi.com/api/1";

const imageUrlCache = new Map<string, string>();

/**
 * Function to get the image URL or fallback to placeholder, with caching.
 * @param imagePath
 * @returns string
 */
export function getImageUrl(imagePath: string | null): string {
  const placeholderImage = `${base}/default_quest_image.png`;

  if (
    !imagePath ||
    imagePath.trim() === "" ||
    imagePath.includes("000000_hr1")
  ) {
    return placeholderImage;
  }

  // Check cache first
  if (imageUrlCache.has(imagePath)) {
    return imageUrlCache.get(imagePath)!;
  }

  try {
    const encodedPath = encodeURIComponent(imagePath);
    const assetPath = `${XIVAPI_BETA_BASE_URL}/asset?path=${encodedPath}&format=png`;

    new URL(assetPath); // validate
    imageUrlCache.set(imagePath, assetPath);
    return assetPath;
  } catch {
    return placeholderImage;
  }
}
