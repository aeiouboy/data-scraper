import { cn } from "../../utils/cn";
import { useEffect, useRef, useState } from "react";

interface NumberTickerProps {
  value: number;
  direction?: "up" | "down";
  delay?: number;
  className?: string;
  decimalPlaces?: number;
}

export function NumberTicker({
  value,
  direction = "up",
  delay = 0,
  className,
  decimalPlaces = 0,
}: NumberTickerProps) {
  const [displayValue, setDisplayValue] = useState(direction === "up" ? 0 : value);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (hasAnimated.current) return;

    const startValue = direction === "up" ? 0 : value;
    const endValue = direction === "up" ? value : 0;
    const duration = 2000; // 2 seconds
    const stepTime = 50; // Update every 50ms
    const steps = duration / stepTime;
    const stepValue = (endValue - startValue) / steps;

    const timer = setTimeout(() => {
      let currentValue = startValue;
      
      intervalRef.current = setInterval(() => {
        currentValue += stepValue;
        
        if (
          (direction === "up" && currentValue >= endValue) ||
          (direction === "down" && currentValue <= endValue)
        ) {
          setDisplayValue(endValue);
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          hasAnimated.current = true;
        } else {
          setDisplayValue(currentValue);
        }
      }, stepTime);
    }, delay);

    return () => {
      clearTimeout(timer);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [value, direction, delay]);

  return (
    <span className={cn("tabular-nums", className)}>
      {Intl.NumberFormat("en-US", {
        minimumFractionDigits: decimalPlaces,
        maximumFractionDigits: decimalPlaces,
      }).format(displayValue)}
    </span>
  );
}