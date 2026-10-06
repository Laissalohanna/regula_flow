export function Logo() {
  return (
    <span className="logo">
      <svg viewBox="0 0 32 32" aria-hidden="true">
        <rect width="32" height="32" rx="8" fill="#1D4ED8" />
        <path fill="#FFFFFF" d="M8 9.5h3.4v13H8z" />
        <path
          d="M14.6 16h6.4M18.6 12.2 23.2 16l-4.6 3.8"
          fill="none"
          stroke="#FFFFFF"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span className="wordmark">
        Regula<strong>Flow</strong>
      </span>
    </span>
  );
}
