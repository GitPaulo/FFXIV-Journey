import { base } from "$app/paths";

export const XIVAPI_BASE_URL = "https://xivapi.com";
export const XIVAPI_BETA_BASE_URL = "https://beta.xivapi.com/api/1";

/**
 * Function to get the image URL or fallback to placeholder
 * @param imagePath 
 * @returns string
 */
export function getImageUrl(imagePath: string | null): string {
  const placeholderImage = `${base}/default_quest_image.png`;
  if (
    !imagePath ||
    imagePath.trim() === "" ||
    imagePath.includes("000000_hr1") // Returned by XIVAPI for missing images
  ) {
    return placeholderImage;
  }
  try {
    const assetPath = `${XIVAPI_BETA_BASE_URL}/asset/${imagePath}?format=png`;
    new URL(assetPath);
    return assetPath;
  } catch {
    return placeholderImage;
  }
}

/**
 * @deprecated
 * Function to get the old image URL or fallback to placeholder
 * @param imagePath 
 * @returns string
 */
export function getOldImageUrl(imagePath: string | null): string {
  if (!imagePath) {
    return "https://fakeimg.pl/300x160/2e2e2e/ab4444?text=Unknown"; // Placeholder unknown
  }
  return `${XIVAPI_BASE_URL}/${imagePath}`;
}
