import { cn } from "../../utils/cn";
import { ReactNode, useRef, useState } from "react";

interface MagicCardProps {
  children: ReactNode;
  className?: string;
  gradientColor?: string;
  gradientOpacity?: number;
  gradientSize?: number;
}

export function MagicCard({
  children,
  className,
  gradientColor = "#3b82f6",
  gradientOpacity = 0.8,
  gradientSize = 200,
}: MagicCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (cardRef.current) {
      const rect = cardRef.current.getBoundingClientRect();
      setMousePosition({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    }
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      className={cn(
        "relative overflow-hidden rounded-lg border border-gray-200 bg-white p-6 shadow-lg transition-all duration-300 hover:shadow-xl",
        className
      )}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 hover:opacity-100"
        style={{
          background: `radial-gradient(${gradientSize}px circle at ${mousePosition.x}px ${mousePosition.y}px, ${gradientColor}${Math.round(gradientOpacity * 255).toString(16).padStart(2, '0')}, transparent)`,
        }}
      />
      <div className="relative z-10">{children}</div>
    </div>
  );
}