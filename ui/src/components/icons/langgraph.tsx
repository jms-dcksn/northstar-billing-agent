import React from "react";

export function LangGraphLogoSVG(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 40 40"
      fill="none"
      aria-label="Northstar Audio"
      role="img"
      {...props}
    >
      <rect
        width="40"
        height="40"
        rx="11"
        fill="#103F3C"
      />
      <path
        d="M20 5l3.8 11.2L35 20l-11.2 3.8L20 35l-3.8-11.2L5 20l11.2-3.8L20 5z"
        fill="#D8ECA3"
      />
      <circle
        cx="20"
        cy="20"
        r="3"
        fill="#103F3C"
      />
    </svg>
  );
}
