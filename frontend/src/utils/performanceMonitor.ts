/**
 * Performance Monitoring Utility
 * Tracks component render times, API call durations, and other performance metrics
 */

interface TimerEntry {
  label: string;
  startTime: number;
  endTime?: number;
  duration?: number;
}

interface PerformanceMetrics {
  [label: string]: {
    count: number;
    totalTime: number;
    minTime: number;
    maxTime: number;
    avgTime: number;
    lastTime: number;
    measurements: number[];
  };
}

class PerformanceMonitor {
  private timers: Map<string, TimerEntry> = new Map();
  private metrics: PerformanceMetrics = {};
  private enabled: boolean = process.env.NODE_ENV === 'development';
  private maxMeasurements: number = 100; // Keep last 100 measurements per label

  /**
   * Start a performance timer
   * @param label - Unique identifier for the timer
   * @param metadata - Optional metadata to attach to the timer
   */
  startTimer(label: string, metadata?: any): void {
    if (!this.enabled) return;

    const timer: TimerEntry = {
      label,
      startTime: performance.now(),
    };

    this.timers.set(label, timer);

    if (metadata) {
      console.debug(`[PerformanceMonitor] Started timer: ${label}`, metadata);
    }
  }

  /**
   * End a performance timer and record the duration
   * @param label - Unique identifier for the timer
   * @returns The duration in milliseconds, or null if timer not found
   */
  endTimer(label: string): number | null {
    if (!this.enabled) return null;

    const timer = this.timers.get(label);
    if (!timer) {
      console.warn(`[PerformanceMonitor] Timer not found: ${label}`);
      return null;
    }

    const endTime = performance.now();
    const duration = endTime - timer.startTime;

    timer.endTime = endTime;
    timer.duration = duration;

    // Update metrics
    this.updateMetrics(label, duration);

    // Clean up timer
    this.timers.delete(label);

    // Log if duration exceeds threshold
    if (duration > 1000) {
      console.warn(`[PerformanceMonitor] Slow operation detected: ${label} took ${duration.toFixed(2)}ms`);
    }

    return duration;
  }

  /**
   * Measure the execution time of a function
   * @param label - Label for the measurement
   * @param fn - Function to measure
   * @returns The result of the function
   */
  async measureAsync<T>(label: string, fn: () => Promise<T>): Promise<T> {
    this.startTimer(label);
    try {
      const result = await fn();
      this.endTimer(label);
      return result;
    } catch (error) {
      this.endTimer(label);
      throw error;
    }
  }

  /**
   * Measure the execution time of a synchronous function
   * @param label - Label for the measurement
   * @param fn - Function to measure
   * @returns The result of the function
   */
  measure<T>(label: string, fn: () => T): T {
    this.startTimer(label);
    try {
      const result = fn();
      this.endTimer(label);
      return result;
    } catch (error) {
      this.endTimer(label);
      throw error;
    }
  }

  /**
   * Update metrics for a given label
   * @param label - Label for the metric
   * @param duration - Duration in milliseconds
   */
  private updateMetrics(label: string, duration: number): void {
    if (!this.metrics[label]) {
      this.metrics[label] = {
        count: 0,
        totalTime: 0,
        minTime: duration,
        maxTime: duration,
        avgTime: duration,
        lastTime: duration,
        measurements: [],
      };
    }

    const metric = this.metrics[label];
    
    // Update measurements array (keep only last N measurements)
    metric.measurements.push(duration);
    if (metric.measurements.length > this.maxMeasurements) {
      metric.measurements.shift();
    }

    // Update statistics
    metric.count++;
    metric.totalTime += duration;
    metric.lastTime = duration;
    metric.minTime = Math.min(metric.minTime, duration);
    metric.maxTime = Math.max(metric.maxTime, duration);
    metric.avgTime = metric.totalTime / metric.count;
  }

  /**
   * Get average time for a specific label
   * @param label - Label to get average for
   * @returns Average time in milliseconds, or null if label not found
   */
  getAverageTime(label: string): number | null {
    const metric = this.metrics[label];
    return metric ? metric.avgTime : null;
  }

  /**
   * Get all metrics for a specific label
   * @param label - Label to get metrics for
   * @returns Metrics object, or null if label not found
   */
  getMetrics(label: string): PerformanceMetrics[string] | null {
    return this.metrics[label] || null;
  }

  /**
   * Get all recorded metrics
   * @returns All performance metrics
   */
  getAllMetrics(): PerformanceMetrics {
    return this.metrics;
  }

  /**
   * Log all metrics to console
   * @param detailed - Whether to include detailed statistics
   */
  logMetrics(detailed: boolean = false): void {
    if (!this.enabled) return;

    console.group('[PerformanceMonitor] Performance Metrics');
    
    const sortedLabels = Object.keys(this.metrics).sort((a, b) => 
      this.metrics[b].avgTime - this.metrics[a].avgTime
    );

    sortedLabels.forEach(label => {
      const metric = this.metrics[label];
      console.log(
        `${label}: avg=${metric.avgTime.toFixed(2)}ms, ` +
        `count=${metric.count}, ` +
        `last=${metric.lastTime.toFixed(2)}ms, ` +
        `min=${metric.minTime.toFixed(2)}ms, ` +
        `max=${metric.maxTime.toFixed(2)}ms`
      );

      if (detailed && metric.measurements.length > 0) {
        const recentMeasurements = metric.measurements.slice(-10);
        console.log(`  Recent measurements: ${recentMeasurements.map(m => m.toFixed(2)).join(', ')}ms`);
      }
    });

    console.groupEnd();
  }

  /**
   * Reset all metrics
   */
  reset(): void {
    this.timers.clear();
    this.metrics = {};
    console.log('[PerformanceMonitor] All metrics reset');
  }

  /**
   * Reset metrics for a specific label
   * @param label - Label to reset
   */
  resetLabel(label: string): void {
    delete this.metrics[label];
    console.log(`[PerformanceMonitor] Metrics reset for: ${label}`);
  }

  /**
   * Enable or disable performance monitoring
   * @param enabled - Whether to enable monitoring
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
    console.log(`[PerformanceMonitor] Monitoring ${enabled ? 'enabled' : 'disabled'}`);
  }

  /**
   * Get percentile value from measurements
   * @param label - Label to calculate percentile for
   * @param percentile - Percentile value (0-100)
   * @returns Percentile value in milliseconds, or null if not enough data
   */
  getPercentile(label: string, percentile: number): number | null {
    const metric = this.metrics[label];
    if (!metric || metric.measurements.length === 0) return null;

    const sorted = [...metric.measurements].sort((a, b) => a - b);
    const index = Math.ceil((percentile / 100) * sorted.length) - 1;
    return sorted[Math.max(0, index)];
  }

  /**
   * Export metrics as JSON
   * @returns JSON string of all metrics
   */
  exportMetrics(): string {
    return JSON.stringify(this.metrics, null, 2);
  }

  /**
   * Create a performance mark (for React DevTools integration)
   * @param label - Label for the mark
   */
  mark(label: string): void {
    if (!this.enabled || !window.performance.mark) return;
    
    try {
      window.performance.mark(label);
    } catch (error) {
      // Ignore errors (some browsers have limits on marks)
    }
  }

  /**
   * Measure between two marks
   * @param label - Label for the measurement
   * @param startMark - Start mark name
   * @param endMark - End mark name
   */
  measureMarks(label: string, startMark: string, endMark: string): void {
    if (!this.enabled || !window.performance.measure) return;

    try {
      window.performance.measure(label, startMark, endMark);
      const entries = window.performance.getEntriesByName(label, 'measure');
      if (entries.length > 0) {
        const duration = entries[entries.length - 1].duration;
        this.updateMetrics(label, duration);
      }
    } catch (error) {
      // Ignore errors
    }
  }
}

// Create singleton instance
const performanceMonitor = new PerformanceMonitor();

// Helper functions for common use cases
export const startTimer = (label: string, metadata?: any) => 
  performanceMonitor.startTimer(label, metadata);

export const endTimer = (label: string) => 
  performanceMonitor.endTimer(label);

export const measureAsync = <T>(label: string, fn: () => Promise<T>) => 
  performanceMonitor.measureAsync(label, fn);

export const measure = <T>(label: string, fn: () => T) => 
  performanceMonitor.measure(label, fn);

export const logMetrics = (detailed?: boolean) => 
  performanceMonitor.logMetrics(detailed);

export const getAverageTime = (label: string) => 
  performanceMonitor.getAverageTime(label);

export const getMetrics = (label: string) => 
  performanceMonitor.getMetrics(label);

export const getAllMetrics = () => 
  performanceMonitor.getAllMetrics();

export const resetMetrics = () => 
  performanceMonitor.reset();

export const getPercentile = (label: string, percentile: number) => 
  performanceMonitor.getPercentile(label, percentile);

// React-specific hooks
export const usePerformanceTimer = (label: string) => {
  return {
    start: (metadata?: any) => startTimer(label, metadata),
    end: () => endTimer(label),
  };
};

// API call monitoring helper
export const monitorAPICall = async <T>(
  endpoint: string,
  request: () => Promise<T>
): Promise<T> => {
  const label = `API: ${endpoint}`;
  return measureAsync(label, request);
};

// Component render monitoring helper
export const monitorComponentRender = (componentName: string) => {
  const label = `Render: ${componentName}`;
  return {
    start: () => startTimer(label),
    end: () => endTimer(label),
  };
};

// Auto-log metrics periodically in development
if (process.env.NODE_ENV === 'development') {
  // Log metrics every 30 seconds
  setInterval(() => {
    const metrics = getAllMetrics();
    if (Object.keys(metrics).length > 0) {
      console.log('[PerformanceMonitor] Periodic metrics report:');
      logMetrics();
    }
  }, 30000);

  // Add to window for debugging
  (window as any).performanceMonitor = {
    logMetrics,
    getMetrics,
    getAllMetrics,
    resetMetrics,
    exportMetrics: () => performanceMonitor.exportMetrics(),
  };
}

export default performanceMonitor;