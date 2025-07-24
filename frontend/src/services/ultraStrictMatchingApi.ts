/**
 * Ultra-Strict Matching API Service
 * Provides maximum accuracy product matching with strict validation
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Types for Ultra-Strict Matching
export interface UltraStrictMatchRequest {
  product_id: string;
  max_results?: number;
  confidence_threshold?: number;
  category_filter?: string;
  retailer_exclusions?: string[];
}

export interface TestMatchRequest {
  product1_id: string;
  product2_id: string;
  category?: string;
}

export interface UltraStrictMatchDetails {
  model_exact_match: boolean;
  brand_exact_match: boolean;
  specification_validation: boolean;
  rejection_reason?: string;
  validation_score: number;
  model_similarity: number;
  brand_similarity: number;
  early_rejection: boolean;
}

export interface UltraStrictMatchResult {
  matched_product: {
    id: string;
    name: string;
    brand: string;
    sku: string;
    specs: Record<string, any>;
    category: string;
    price: number;
    retailer_code: string;
    url: string;
  };
  confidence: number;
  match_type: 'exact' | 'high' | 'medium' | 'low' | 'none';
  matched_fields: string[];
  warnings: string[];
  rejection_reasons: string[];
  ultra_strict_details: UltraStrictMatchDetails;
  score_breakdown: {
    sku_score: number;
    brand_score: number;
    name_score: number;
    spec_score: number;
    category_score: number;
    weighted_confidence: number;
    model_penalty: number;
  };
  price_comparison?: {
    target_price: number;
    candidate_price: number;
    price_difference: number;
    price_variance: number;
    savings: number;
    is_better_deal: boolean;
  };
}

export interface UltraStrictMatchResponse {
  query_product: {
    id: string;
    name: string;
    brand: string;
    sku: string;
    specs: Record<string, any>;
    category: string;
    price: number;
    retailer_code: string;
    url: string;
  };
  matches: UltraStrictMatchResult[];
  total_candidates: number;
  matches_found: number;
  processing_time_ms: number;
  matcher_config: {
    type: string;
    version: string;
    accuracy_focus: string;
    false_positive_prevention: string;
    model_validation: string;
    brand_matching: string;
    specification_tolerance: string;
  };
}

export interface UltraStrictConfig {
  matcher_type: string;
  version: string;
  thresholds: {
    exact: number;
    high: number;
    medium: number;
    low: number;
    minimum: number;
  };
  weights: {
    sku: number;
    brand: number;
    name: number;
    specs: number;
    category: number;
  };
  tolerances: {
    'air-conditioner': {
      btu: number;
      power: number;
      capacity: number;
    };
    refrigerator: {
      capacity: number;
      volume: number;
    };
    default: {
      size: number;
      capacity: number;
      power: number;
    };
  };
  features: string[];
}

export interface MatcherComparison {
  standard_result?: any;
  optimized_result?: any;
  ultra_strict_result: UltraStrictMatchResult;
  recommendation: 'ultra_strict' | 'optimized' | 'standard';
  confidence_comparison: {
    standard: number;
    optimized: number;
    ultra_strict: number;
  };
}

class UltraStrictMatchingApi {
  private baseUrl = '/api/matching-ultra-strict';

  /**
   * Find ultra-strict matches for a product
   */
  async findMatches(request: UltraStrictMatchRequest): Promise<UltraStrictMatchResponse> {
    try {
      const response = await api.post<UltraStrictMatchResponse>(
        `${this.baseUrl}/find-matches`,
        request
      );
      return response.data;
    } catch (error) {
      console.error('Error finding ultra-strict matches:', error);
      throw error;
    }
  }

  /**
   * Test matching between two specific products
   */
  async testMatch(request: TestMatchRequest): Promise<UltraStrictMatchResult> {
    try {
      const response = await api.post<UltraStrictMatchResult>(
        `${this.baseUrl}/test-match`,
        request
      );
      return response.data;
    } catch (error) {
      console.error('Error testing ultra-strict match:', error);
      throw error;
    }
  }

  /**
   * Get ultra-strict matcher configuration
   */
  async getConfig(): Promise<UltraStrictConfig> {
    try {
      const response = await api.get<UltraStrictConfig>(`${this.baseUrl}/config`);
      return response.data;
    } catch (error) {
      console.error('Error getting ultra-strict config:', error);
      throw error;
    }
  }

  /**
   * Check health of ultra-strict matching service
   */
  async healthCheck(): Promise<{ status: string; matcher_type: string; version: string; timestamp: string }> {
    try {
      const response = await api.get(`${this.baseUrl}/health`);
      return response.data;
    } catch (error) {
      console.error('Error checking ultra-strict service health:', error);
      throw error;
    }
  }

  /**
   * Compare matching results across different matchers
   */
  async compareMatchers(
    product1_id: string,
    product2_id: string,
    category?: string
  ): Promise<MatcherComparison> {
    try {
      const testRequest: TestMatchRequest = {
        product1_id,
        product2_id,
        category
      };

      // Get ultra-strict result
      const ultraStrictResult = await this.testMatch(testRequest);

      // TODO: Add calls to other matchers when needed
      // const optimizedResult = await optimizedMatchingApi.testMatch(testRequest);
      // const standardResult = await standardMatchingApi.testMatch(testRequest);

      // Determine recommendation based on confidence and validation
      let recommendation: 'ultra_strict' | 'optimized' | 'standard' = 'ultra_strict';
      
      // Ultra-strict is recommended when:
      // - High confidence with validation
      // - Low false positive risk
      // - Strict model/brand validation needed
      if (ultraStrictResult.confidence > 0.8 && ultraStrictResult.ultra_strict_details.specification_validation) {
        recommendation = 'ultra_strict';
      } else if (ultraStrictResult.confidence < 0.3 && ultraStrictResult.rejection_reasons.length > 0) {
        recommendation = 'ultra_strict'; // Still recommended for rejection clarity
      }

      return {
        ultra_strict_result: ultraStrictResult,
        recommendation,
        confidence_comparison: {
          standard: 0, // TODO: Add when available
          optimized: 0, // TODO: Add when available
          ultra_strict: ultraStrictResult.confidence
        }
      };
    } catch (error) {
      console.error('Error comparing matchers:', error);
      throw error;
    }
  }

  /**
   * Get match confidence level description
   */
  getConfidenceDescription(confidence: number, matchType: string): string {
    if (matchType === 'exact') {
      return 'Exact Match - Identical products';
    } else if (matchType === 'high') {
      return 'High Confidence - Very likely same product';
    } else if (matchType === 'medium') {
      return 'Medium Confidence - Probably same product';
    } else if (matchType === 'low') {
      return 'Low Confidence - Possibly same product';
    } else {
      return 'No Match - Different products';
    }
  }

  /**
   * Get confidence level color for UI
   */
  getConfidenceColor(confidence: number, matchType: string): string {
    if (matchType === 'exact') {
      return '#4CAF50'; // Green
    } else if (matchType === 'high') {
      return '#2196F3'; // Blue
    } else if (matchType === 'medium') {
      return '#FF9800'; // Orange
    } else if (matchType === 'low') {
      return '#FF5722'; // Red-Orange
    } else {
      return '#F44336'; // Red
    }
  }

  /**
   * Format rejection reasons for display
   */
  formatRejectionReasons(reasons: string[]): string {
    if (reasons.length === 0) return 'No rejection reasons';
    
    return reasons.map(reason => {
      // Make rejection reasons more user-friendly
      return reason
        .replace('Model mismatch:', 'Different models:')
        .replace('Brand mismatch:', 'Different brands:')
        .replace('BTU mismatch:', 'Different BTU ratings:')
        .replace('similarity:', 'similarity score:');
    }).join('; ');
  }

  /**
   * Get validation status icon
   */
  getValidationIcon(details: UltraStrictMatchDetails): string {
    if (details.specification_validation && details.model_exact_match && details.brand_exact_match) {
      return '✅'; // All validations passed
    } else if (details.specification_validation) {
      return '⚠️'; // Partial validation
    } else if (details.early_rejection) {
      return '❌'; // Early rejection
    } else {
      return '🔍'; // Under review
    }
  }

  /**
   * Calculate match quality score (0-100)
   */
  calculateMatchQuality(result: UltraStrictMatchResult): number {
    const { ultra_strict_details, confidence, warnings, rejection_reasons } = result;
    
    let quality = confidence * 100;
    
    // Boost for exact matches
    if (ultra_strict_details.model_exact_match) quality += 5;
    if (ultra_strict_details.brand_exact_match) quality += 5;
    if (ultra_strict_details.specification_validation) quality += 5;
    
    // Penalty for warnings and rejections
    quality -= warnings.length * 2;
    quality -= rejection_reasons.length * 10;
    
    // Penalty for early rejection
    if (ultra_strict_details.early_rejection) quality -= 20;
    
    return Math.max(0, Math.min(100, quality));
  }
}

// Export singleton instance
export const ultraStrictMatchingApi = new UltraStrictMatchingApi();

// Export types for use in components
export type {
  UltraStrictMatchRequest as UltraStrictMatchRequestType,
  TestMatchRequest as TestMatchRequestType,
  UltraStrictMatchDetails as UltraStrictMatchDetailsType,
  UltraStrictMatchResult as UltraStrictMatchResultType,
  UltraStrictMatchResponse as UltraStrictMatchResponseType,
  UltraStrictConfig as UltraStrictConfigType,
  MatcherComparison as MatcherComparisonType
};