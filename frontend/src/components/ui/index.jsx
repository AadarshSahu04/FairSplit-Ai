/**
 * Spinner.jsx — Loading indicator component.
 */
export function Spinner({ size = 'md', label = 'Loading…' }) {
  return (
    <span
      className={`spinner${size === 'lg' ? ' spinner-lg' : ''}`}
      role="status"
      aria-label={label}
    />
  );
}

/**
 * Alert.jsx — Contextual status message.
 */
export function Alert({ variant = 'info', icon, children }) {
  const icons = { info: 'ℹ️', success: '✅', warning: '⚠️', error: '❌' };
  return (
    <div className={`alert alert-${variant}`} role="alert">
      <span className="alert-icon" aria-hidden="true">{icon ?? icons[variant]}</span>
      <div>{children}</div>
    </div>
  );
}

/**
 * Badge.jsx — Compact status label.
 */
export function Badge({ variant = 'neutral', children }) {
  return <span className={`badge badge-${variant}`}>{children}</span>;
}

/**
 * Button.jsx — Versatile button component.
 */
export function Button({
  children,
  variant = 'primary',
  size,
  full = false,
  disabled = false,
  type = 'button',
  onClick,
  id,
  className = '',
  ...props
}) {
  const classes = [
    'btn',
    `btn-${variant}`,
    size ? `btn-${size}` : '',
    full ? 'btn-full' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <button
      type={type}
      className={classes}
      disabled={disabled}
      onClick={onClick}
      id={id}
      {...props}
    >
      {children}
    </button>
  );
}

/**
 * Card.jsx — Surface container.
 */
export function Card({ children, elevated = false, className = '', style }) {
  return (
    <div
      className={`card${elevated ? ' card-elevated' : ''} ${className}`}
      style={style}
    >
      {children}
    </div>
  );
}
