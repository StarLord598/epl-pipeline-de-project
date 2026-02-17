import { TEAM_SHORT, TEAM_COLORS } from "@/lib/data";

interface TeamBadgeProps {
  teamName: string;
  size?: "sm" | "md" | "lg";
  showName?: boolean;
}

export default function TeamBadge({ teamName, size = "md", showName = false }: TeamBadgeProps) {
  const colors = TEAM_COLORS[teamName] || { primary: "#6b7280", secondary: "#374151", text: "#fff" };
  const abbr = TEAM_SHORT[teamName] || teamName.slice(0, 3).toUpperCase();

  const sizeClasses = {
    sm: "w-7 h-7 text-xs",
    md: "w-9 h-9 text-xs",
    lg: "w-12 h-12 text-sm",
  };

  return (
    <div className="flex items-center gap-2">
      <div
        className={`${sizeClasses[size]} rounded-full flex items-center justify-center font-black flex-shrink-0`}
        style={{ background: colors.primary, color: colors.text }}
      >
        {abbr}
      </div>
      {showName && (
        <span className="font-medium text-white">{teamName}</span>
      )}
    </div>
  );
}
