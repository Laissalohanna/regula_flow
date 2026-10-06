export function Logo() {
  return (
    <span className="logo">
      <svg viewBox="0 0 32 32" aria-hidden="true">
        <rect width="32" height="32" rx="8" fill="#18483b" />
        <path
          d="M8 18.2c2.4-5 5.4-7.4 8.6-7.4 2.6 0 4.4 1.4 5.6 3.4"
          fill="none"
          stroke="#d9f6ec"
          strokeWidth="2.2"
          strokeLinecap="round"
        />
        <path
          d="M9.2 17.4 13.6 22l9-11.2"
          fill="none"
          stroke="#3dbe9a"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span>
        Regula<b>Flow</b>
      </span>
    </span>
  );
}
