import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback, useRef } from 'react';
import { retailerApi } from '../services/api';
import { useQuery } from '@tanstack/react-query';

// Retailer Types
export interface Retailer {
  id: string;
  code: string;
  name: string;
  base_url: string;
  market_position: string;
  estimated_products: number;
  rate_limit_delay: number;
  max_concurrent: number;
  focus_categories: string[];
  price_volatility: string;
  is_active: boolean;
}

export interface RetailerStats {
  code: string;
  name: string;
  actual_products: number;
  in_stock_products: number;
  priced_products: number;
  avg_price: number;
  min_price: number;
  max_price: number;
  ultra_critical_count: number;
  high_value_count: number;
  standard_count: number;
  low_priority_count: number;
  category_coverage_percentage: number;
  brand_coverage_percentage: number;
  last_scraped_at: string;
}

interface RetailerContextType {
  // Current Selection
  selectedRetailer: string | null;
  setSelectedRetailer: (retailerCode: string | null) => void;
  
  // Retailer Data
  retailers: Retailer[];
  retailerStats: RetailerStats[];
  
  // Loading States
  isLoadingRetailers: boolean;
  isLoadingStats: boolean;
  
  // Helper Functions
  getRetailerByCode: (code: string) => Retailer | undefined;
  getRetailerStats: (code: string) => RetailerStats | undefined;
  getActiveRetailers: () => Retailer[];
  
  // Multi-Retailer Mode
  multiRetailerMode: boolean;
  setMultiRetailerMode: (enabled: boolean) => void;
  selectedRetailers: string[];
  setSelectedRetailers: (retailers: string[]) => void;
}

const RetailerContext = createContext<RetailerContextType | undefined>(undefined);

export const useRetailer = () => {
  const context = useContext(RetailerContext);
  if (context === undefined) {
    throw new Error('useRetailer must be used within a RetailerProvider');
  }
  return context;
};

interface RetailerProviderProps {
  children: ReactNode;
}

export const RetailerProvider: React.FC<RetailerProviderProps> = ({ children }) => {
  // State Management
  const [selectedRetailer, setSelectedRetailer] = useState<string | null>('HP'); // Default to HomePro
  const [multiRetailerMode, setMultiRetailerMode] = useState(false);
  const [selectedRetailers, setSelectedRetailers] = useState<string[]>(['HP']);
  
  // Track initialization to prevent loops
  const isInitialized = useRef(false);

  // Fetch Retailers
  const { data: retailers = [], isLoading: isLoadingRetailers } = useQuery({
    queryKey: ['retailers'],
    queryFn: async () => {
      const response = await retailerApi.getAll();
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Fetch Retailer Summary/Stats
  const { data: retailerStats = [], isLoading: isLoadingStats } = useQuery({
    queryKey: ['retailer-stats'],
    queryFn: async () => {
      const response = await retailerApi.getSummary();
      return response.data;
    },
    refetchInterval: 30 * 1000, // Refresh every 30 seconds
  });

  // Helper Functions
  const getRetailerByCode = (code: string): Retailer | undefined => {
    return retailers.find((retailer: Retailer) => retailer.code === code);
  };

  const getRetailerStats = (code: string): RetailerStats | undefined => {
    return retailerStats.find((stats: RetailerStats) => stats.code === code);
  };

  const getActiveRetailers = useCallback((): Retailer[] => {
    return retailers.filter((retailer: Retailer) => retailer.is_active);
  }, [retailers]);

  // Initialize default retailer only once when retailers are loaded
  useEffect(() => {
    if (!isInitialized.current && retailers.length > 0) {
      isInitialized.current = true;
      
      // If no retailer is selected, set default
      if (!selectedRetailer) {
        const activeRetailers = getActiveRetailers();
        const defaultRetailer = activeRetailers.find(r => r.code === 'HP') || activeRetailers[0];
        if (defaultRetailer) {
          setSelectedRetailer(defaultRetailer.code);
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [retailers]); // Only depend on retailers loading, not selectedRetailer or getActiveRetailers

  // Sync selectedRetailers based on mode changes
  useEffect(() => {
    if (multiRetailerMode) {
      // Get all active retailer codes
      const activeRetailerCodes = getActiveRetailers().map(r => r.code);
      // Only update if different
      setSelectedRetailers(prev => {
        const prevSorted = [...prev].sort();
        const newSorted = [...activeRetailerCodes].sort();
        if (prevSorted.length !== newSorted.length || 
            prevSorted.some((code, i) => code !== newSorted[i])) {
          return activeRetailerCodes;
        }
        return prev;
      });
    } else if (selectedRetailer) {
      // Single mode: only include the selected retailer
      setSelectedRetailers(prev => {
        if (prev.length !== 1 || prev[0] !== selectedRetailer) {
          return [selectedRetailer];
        }
        return prev;
      });
    }
  }, [multiRetailerMode, selectedRetailer, getActiveRetailers]);

  const contextValue: RetailerContextType = {
    // Current Selection
    selectedRetailer,
    setSelectedRetailer,
    
    // Retailer Data
    retailers,
    retailerStats,
    
    // Loading States
    isLoadingRetailers,
    isLoadingStats,
    
    // Helper Functions
    getRetailerByCode,
    getRetailerStats,
    getActiveRetailers,
    
    // Multi-Retailer Mode
    multiRetailerMode,
    setMultiRetailerMode,
    selectedRetailers,
    setSelectedRetailers,
  };

  return (
    <RetailerContext.Provider value={contextValue}>
      {children}
    </RetailerContext.Provider>
  );
};

// Convenience Hooks
export const useSelectedRetailer = () => {
  const { selectedRetailer, getRetailerByCode } = useRetailer();
  return selectedRetailer ? getRetailerByCode(selectedRetailer) : undefined;
};

export const useSelectedRetailerStats = () => {
  const { selectedRetailer, getRetailerStats } = useRetailer();
  return selectedRetailer ? getRetailerStats(selectedRetailer) : undefined;
};

export const useRetailerList = () => {
  const { retailers, getActiveRetailers } = useRetailer();
  return {
    allRetailers: retailers,
    activeRetailers: getActiveRetailers(),
  };
};

export default RetailerContext;