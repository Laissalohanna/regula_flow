export function Logo() {
  return (
    <span className="logo">
      <svg viewBox="0 0 40 40" aria-hidden="true">
        <rect width="40" height="40" rx="10" fill="#F3EDE3" />
        <path
          fill="#1A1814"
          fillRule="evenodd"
          d="M12.5 31V10h8.6c4.2 0 6.9 2.2 6.9 5.7 0 2.8-1.8 4.8-4.5 5.4L30 31h-4.8l-5.4-9.2h-2.5V31h-4.8zm4.8-13.6h4c1.9 0 3.1-1 3.1-2.5s-1.2-2.5-3.1-2.5h-4v5z"
        />
        <path
          d="M23 28.2c2.8-1.5 5.4-1.3 8.2.6"
          fill="none"
          stroke="#B08D4E"
          strokeWidth="1.7"
          strokeLinecap="round"
        />
      </svg>
      <span className="wordmark">
        <strong>Regula</strong>
        <em>Flow</em>
      </span>
    </span>
  );
}
