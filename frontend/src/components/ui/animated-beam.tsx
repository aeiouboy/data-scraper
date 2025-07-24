import { cn } from "../../utils/cn";
import React, { useEffect, useRef, useState } from "react";

interface AnimatedBeamProps {
  className?: string;
  containerRef: React.RefObject<HTMLDivElement>;
  fromRef: React.RefObject<HTMLElement>;
  toRef: React.RefObject<HTMLElement>;
  curvature?: number;
  reverse?: boolean;
  duration?: number;
  delay?: number;
  pathColor?: string;
  pathWidth?: number;
  pathOpacity?: number;
  gradientStartColor?: string;
  gradientStopColor?: string;
  startXOffset?: number;
  startYOffset?: number;
  endXOffset?: number;
  endYOffset?: number;
}

export function AnimatedBeam({
  className,
  containerRef,
  fromRef,
  toRef,
  curvature = 0,
  reverse = false,
  duration = 2,
  delay = 0,
  pathColor = "gray",
  pathWidth = 2,
  pathOpacity = 0.2,
  gradientStartColor = "#3b82f6",
  gradientStopColor = "#8b5cf6",
  startXOffset = 0,
  startYOffset = 0,
  endXOffset = 0,
  endYOffset = 0,
}: AnimatedBeamProps) {
  const [pathD, setPathD] = useState("");
  const [svgDimensions, setSvgDimensions] = useState({ width: 0, height: 0 });
  const pathRef = useRef<SVGPathElement>(null);

  useEffect(() => {
    const updatePath = () => {
      if (containerRef.current && fromRef.current && toRef.current) {
        const containerRect = containerRef.current.getBoundingClientRect();
        const fromRect = fromRef.current.getBoundingClientRect();
        const toRect = toRef.current.getBoundingClientRect();

        const startX = fromRect.left - containerRect.left + fromRect.width / 2 + startXOffset;
        const startY = fromRect.top - containerRect.top + fromRect.height / 2 + startYOffset;
        const endX = toRect.left - containerRect.left + toRect.width / 2 + endXOffset;
        const endY = toRect.top - containerRect.top + toRect.height / 2 + endYOffset;

        const controlX = startX + (endX - startX) / 2;
        const controlY = startY + (endY - startY) / 2 + curvature;

        const d = `M ${startX} ${startY} Q ${controlX} ${controlY} ${endX} ${endY}`;
        setPathD(d);

        setSvgDimensions({
          width: containerRect.width,
          height: containerRect.height,
        });
      }
    };

    updatePath();
    const resizeObserver = new ResizeObserver(updatePath);
    
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, [containerRef, fromRef, toRef, curvature, startXOffset, startYOffset, endXOffset, endYOffset]);

  return (
    <svg
      fill="none"
      width={svgDimensions.width}
      height={svgDimensions.height}
      xmlns="http://www.w3.org/2000/svg"
      className={cn(
        "pointer-events-none absolute left-0 top-0 transform-gpu stroke-2",
        className
      )}
      viewBox={`0 0 ${svgDimensions.width} ${svgDimensions.height}`}
    >
      <defs>
        <linearGradient
          id={`gradient-${Math.random()}`}
          gradientUnits="userSpaceOnUse"
          x1="0%"
          x2="100%"
          y1="0%"
          y2="0%"
        >
          <stop offset="0%" stopColor={gradientStartColor} />
          <stop offset="100%" stopColor={gradientStopColor} />
        </linearGradient>
      </defs>
      <path
        d={pathD}
        stroke={pathColor}
        strokeWidth={pathWidth}
        strokeOpacity={pathOpacity}
        fill="none"
      />
      <path
        ref={pathRef}
        d={pathD}
        stroke={`url(#gradient-${Math.random()})`}
        strokeWidth={pathWidth}
        fill="none"
        strokeDasharray="20 20"
        className="animate-pulse"
        style={{
          strokeDashoffset: reverse ? -40 : 40,
          animation: `beam ${duration}s linear infinite`,
          animationDelay: `${delay}s`,
        }}
      />
    </svg>
  );
}