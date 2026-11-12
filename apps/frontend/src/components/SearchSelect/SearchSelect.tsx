import { useId, useState } from 'react';
import styles from './SearchSelect.module.scss';

export interface SearchSelectOption {
  id: number;
  label: string;
  description?: string;
}

interface SearchSelectProps {
  label: string;
  value: string;
  onInputChange: (value: string) => void;
  onSelect: (id: number) => void;
  options: SearchSelectOption[];
  message?: string;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
}

export function SearchSelect({
  label,
  value,
  onInputChange,
  onSelect,
  options,
  message,
  placeholder,
  disabled,
  error,
}: SearchSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const id = useId();
  const listId = `${id}-list`;

  const hasList = isOpen && !disabled && (Boolean(message) || options.length > 0);

  const handleSelect = (optionId: number) => {
    onSelect(optionId);
    setIsOpen(false);
  };

  return (
    <div className={styles.select}>
      <label className={styles.select__label} htmlFor={id}>
        {label}
      </label>

      <div className={styles.select__control}>
        <input
          id={id}
          className={`${styles.select__input} ${error ? styles['select__input--error'] : ''}`}
          type="text"
          role="combobox"
          aria-expanded={hasList}
          aria-controls={listId}
          aria-autocomplete="list"
          autoComplete="off"
          value={value}
          placeholder={placeholder}
          disabled={disabled}
          onChange={(event) => {
            onInputChange(event.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onClick={() => setIsOpen(true)}
          onBlur={() => setIsOpen(false)}
          onKeyDown={(event) => {
            if (event.key === 'Escape') {
              setIsOpen(false);
            }
          }}
        />

        <svg
          className={`${styles.select__chevron} ${
            hasList ? styles['select__chevron--open'] : ''
          }`}
          viewBox="0 0 24 24"
          width="20"
          height="20"
          aria-hidden="true"
        >
          <path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="1.5" />
        </svg>

        {hasList && (
          <ul id={listId} className={styles.select__list}>
            {message ? (
              <li className={styles.select__message}>{message}</li>
            ) : (
              options.map((option) => (
                <li key={option.id}>
                  <button
                    type="button"
                    className={styles.select__option}
                    onMouseDown={(event) => event.preventDefault()}
                    onClick={() => handleSelect(option.id)}
                  >
                    <span>{option.label}</span>
                    {option.description && (
                      <span className={styles.select__optionDescription}>
                        {option.description}
                      </span>
                    )}
                  </button>
                </li>
              ))
            )}
          </ul>
        )}
      </div>

      {error && <p className={styles.select__error}>{error}</p>}
    </div>
  );
}