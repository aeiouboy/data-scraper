import { cn } from "../../utils/cn";

interface ShimmerButtonProps {
  children: React.ReactNode;
  className?: string;
  shimmerColor?: string;
  shimmerSize?: string;
  borderRadius?: string;
  shimmerDuration?: string;
  background?: string;
  onClick?: () => void;
}

export function ShimmerButton({
  children,
  className,
  shimmerColor = "rgba(255, 255, 255, 0.5)",
  shimmerSize = "100%",
  borderRadius = "8px",
  shimmerDuration = "3s",
  background = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  onClick,
}: ShimmerButtonProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "relative inline-flex items-center justify-center overflow-hidden rounded-lg border border-gray-300 bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-3 text-white font-medium transition-all duration-300 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed",
        className
      )}
      style={{
        background,
        borderRadius,
      }}
    >
      <span className="relative z-10">{children}</span>
      <div
        className="absolute inset-0 -top-2 -left-2 h-[calc(100%+16px)] w-[calc(100%+16px)] bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-0 transition-opacity duration-300 hover:opacity-100"
        style={{
          background: `linear-gradient(45deg, transparent, ${shimmerColor}, transparent)`,
          animation: `shimmer ${shimmerDuration} infinite linear`,
        }}
      />
    </button>
  );
}