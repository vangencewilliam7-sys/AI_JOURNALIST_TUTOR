import React, { useState, useRef, useEffect } from 'react';

interface AutocompleteInputProps {
  value: string | number;
  onChange: (val: string) => void;
  suggestions: (string | number)[];
  placeholder?: string;
  type?: string;
  required?: boolean;
  className?: string;
  style?: React.CSSProperties;
  isTextarea?: boolean;
}

const AutocompleteInput: React.FC<AutocompleteInputProps> = ({
  value,
  onChange,
  suggestions,
  placeholder,
  type = 'text',
  required,
  className,
  style,
  isTextarea = false,
}) => {
  const [open, setOpen] = useState(false);
  const [filtered, setFiltered] = useState<(string | number)[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const query = String(value).toLowerCase();
    const matches = suggestions.filter(s =>
      String(s).toLowerCase().includes(query) && String(s) !== String(value)
    );
    setFiltered(matches.slice(0, 6));
  }, [value, suggestions]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSelect = (item: string | number) => {
    onChange(String(item));
    setOpen(false);
  };

  const showDropdown = open && filtered.length > 0;

  const inputProps = {
    required,
    className,
    style,
    placeholder,
    value: value === 0 ? '' : value,
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => onChange(e.target.value),
    onFocus: () => setOpen(true),
  };

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%' }}>
      {isTextarea ? (
        <textarea {...(inputProps as React.TextareaHTMLAttributes<HTMLTextAreaElement>)} />
      ) : (
        <input type={type} {...(inputProps as React.InputHTMLAttributes<HTMLInputElement>)} />
      )}

      {showDropdown && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          zIndex: 1000,
          background: 'var(--bg-card, #1a1a2e)',
          border: '1px solid var(--accent, #6366f1)',
          borderRadius: '6px',
          boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
          overflow: 'hidden',
          marginTop: '4px',
        }}>
          {filtered.map((item, i) => (
            <div
              key={i}
              onMouseDown={() => handleSelect(item)}
              style={{
                padding: '9px 14px',
                fontSize: '13px',
                cursor: 'pointer',
                color: 'var(--text, #e2e8f0)',
                borderBottom: i < filtered.length - 1 ? '1px solid var(--border, #2d2d4e)' : 'none',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                transition: 'background 0.15s',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--accent-muted, rgba(99,102,241,0.15))')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              {String(item)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AutocompleteInput;
