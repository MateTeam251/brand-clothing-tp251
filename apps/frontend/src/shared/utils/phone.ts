export const normalizePhone = (value: string): string => {
  const trimmed = value.trim();
  const digits = trimmed.replace(/\D/g, '');

  if (!digits) {
    return '';
  }

  if (trimmed.startsWith('+') || digits.startsWith('380')) {
    return `+${digits}`;
  }

  if (digits.length === 10 && digits.startsWith('0')) {
    return `+38${digits}`;
  }

  if (digits.length === 9) {
    return `+380${digits}`;
  }

  return `+${digits}`;
};

export const isValidPhone = (value: string): boolean => /^\+\d{9,15}$/.test(value);