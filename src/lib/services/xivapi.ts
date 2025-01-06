import { base } from "$app/paths";

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
    // Encode the imagePath for the new API query parameter
    const encodedPath = encodeURIComponent(imagePath);
    const assetPath = `${XIVAPI_BETA_BASE_URL}/asset?path=${encodedPath}&format=png`;

    // Validate the URL
    new URL(assetPath);
    return assetPath;
  } catch {
    return placeholderImage;
  }
}
