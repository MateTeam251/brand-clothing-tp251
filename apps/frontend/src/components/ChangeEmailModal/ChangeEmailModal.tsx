import { useState } from 'react';
import type { SyntheticEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useChangeEmailMutation } from '../../shared/api/userApi';
import { AuthField } from '../AuthField';
import { AuthMessageCard } from '../AuthMessageCard';
import { AuthModalForm } from '../AuthModalForm';

const EMAIL_PATTERN = /^\S+@\S+\.\S+$/;

const FIELD_KEYS = ['new_email', 'password'] as const;

type FieldKey = (typeof FIELD_KEYS)[number];
type FieldErrors = Partial<Record<FieldKey, string>>;

const mapServerErrors = (data: unknown): FieldErrors => {
  const result: FieldErrors = {};

  if (!data || typeof data !== 'object') {
    return result;
  }

  FIELD_KEYS.forEach((key) => {
    const value = (data as Record<string, unknown>)[key];
    const message = Array.isArray(value) ? value.join(' ') : value;

    if (typeof message === 'string') {
      result[key] = message;
    }
  });

  return result;
};

interface ChangeEmailModalProps {
  currentEmail: string;
  onClose: () => void;
}

export const ChangeEmailModal = ({ currentEmail, onClose }: ChangeEmailModalProps) => {
  const { t } = useTranslation();
  const [changeEmail, { isLoading }] = useChangeEmailMutation();

  const [newEmail, setNewEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSent, setIsSent] = useState(false);

  const handleSubmit = async (event: SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedEmail = newEmail.trim();
    const errors: FieldErrors = {};

    if (!trimmedEmail) {
      errors.new_email = t('auth.errors.required');
    } else if (!EMAIL_PATTERN.test(trimmedEmail)) {
      errors.new_email = t('change_email.errors.invalid_email');
    } else if (trimmedEmail.toLowerCase() === currentEmail.toLowerCase()) {
      errors.new_email = t('change_email.errors.same_email');
    }

    if (!password) {
      errors.password = t('auth.errors.required');
    }

    setFieldErrors(errors);
    setFormError(null);

    if (Object.keys(errors).length > 0) {
      return;
    }

    try {
      await changeEmail({ new_email: trimmedEmail, password }).unwrap();

      setIsSent(true);
    } catch (error) {
      const { status, data } = error as { status?: number; data?: unknown };

      if (status === 400) {
        const serverErrors = mapServerErrors(data);

        if (Object.keys(serverErrors).length > 0) {
          setFieldErrors(serverErrors);
        } else {
          setFormError(t('auth.errors.generic'));
        }
      } else if (status === 429) {
        setFormError(t('auth.errors.too_many_requests'));
      } else {
        setFormError(t('auth.errors.generic'));
      }
    }
  };

  if (isSent) {
    return (
      <AuthMessageCard
        variant="mail"
        title={t('change_email.success_title')}
        text={t('change_email.success_text')}
        primaryLabel={t('change_email.done')}
        onPrimaryClick={onClose}
        onClose={onClose}
      />
    );
  }

  return (
    <AuthMessageCard
      title={t('change_email.title')}
      text={t('change_email.subtitle')}
      onClose={onClose}
    >
      <AuthModalForm
        onSubmit={handleSubmit}
        submitLabel={t('change_email.submit')}
        isSubmitting={isLoading}
        error={formError}
      >
        <AuthField
          name="new_email"
          type="email"
          label={t('change_email.new_email')}
          value={newEmail}
          onChange={setNewEmail}
          error={fieldErrors.new_email}
          autoComplete="email"
        />
        <AuthField
          name="password"
          type="password"
          label={t('change_email.password')}
          value={password}
          onChange={setPassword}
          error={fieldErrors.password}
          autoComplete="current-password"
        />
      </AuthModalForm>
    </AuthMessageCard>
  );
};