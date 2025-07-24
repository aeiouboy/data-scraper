/**
 * Utility functions for retailer detection
 */

/**
 * Detect retailer code from URL
 * @param url - URL to detect retailer from
 * @returns Retailer code or undefined if not detected
 */
export function detectRetailerFromUrl(url: string | undefined): string | undefined {
  if (!url) return undefined;

  // Normalize URL to lowercase for comparison
  const lowerUrl = url.toLowerCase();

  // Check for each retailer's domain
  if (lowerUrl.includes('homepro.co.th')) {
    return 'HP';
  } else if (lowerUrl.includes('thaiwatsadu.com')) {
    return 'TWD';
  } else if (lowerUrl.includes('globalhouse.co.th')) {
    return 'GH';
  } else if (lowerUrl.includes('dohome.co.th')) {
    return 'DH';
  } else if (lowerUrl.includes('boonthavorn.com')) {
    return 'BT';
  } else if (lowerUrl.includes('megahome.co.th')) {
    return 'MH';
  }

  return undefined;
}

/**
 * Get retailer name from code
 * @param code - Retailer code
 * @returns Retailer name
 */
export function getRetailerName(code: string): string {
  const retailers: Record<string, string> = {
    'HP': 'HomePro',
    'TWD': 'Thai Watsadu',
    'GH': 'Global House',
    'DH': 'DoHome',
    'BT': 'Boonthavorn',
    'MH': 'MegaHome',
  };

  return retailers[code] || code;
}