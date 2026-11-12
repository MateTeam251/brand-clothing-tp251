import { useState } from 'react';
import type { SyntheticEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useChangePasswordMutation } from '../../shared/api/userApi';
import { AuthField } from '../AuthField';
import { AuthMessageCard } from '../AuthMessageCard';
import { AuthModalForm } from '../AuthModalForm';

const MIN_PASSWORD_LENGTH = 8;

const FIELD_KEYS = ['old_password', 'new_password', 'new_password_confirm'] as const;

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

interface ChangePasswordModalProps {
  onClose: () => void;
}

export const ChangePasswordModal = ({ onClose }: ChangePasswordModalProps) => {
  const { t } = useTranslation();
  const [changePassword, { isLoading }] = useChangePasswordMutation();

  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isChanged, setIsChanged] = useState(false);

  const handleSubmit = async (event: SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault();

    const errors: FieldErrors = {};

    if (!oldPassword) {
      errors.old_password = t('auth.errors.required');
    }

    if (!newPassword) {
      errors.new_password = t('auth.errors.required');
    } else if (newPassword.length < MIN_PASSWORD_LENGTH) {
      errors.new_password = t('change_password.errors.too_short');
    }

    if (!newPasswordConfirm) {
      errors.new_password_confirm = t('auth.errors.required');
    } else if (newPassword !== newPasswordConfirm) {
      errors.new_password_confirm = t('sign_up.errors.password_mismatch');
    }

    setFieldErrors(errors);
    setFormError(null);

    if (Object.keys(errors).length > 0) {
      return;
    }

    try {
      await changePassword({
        old_password: oldPassword,
        new_password: newPassword,
        new_password_confirm: newPasswordConfirm,
      }).unwrap();

      setIsChanged(true);
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

  if (isChanged) {
    return (
      <AuthMessageCard
        variant="success"
        title={t('change_password.success_title')}
        text={t('change_password.success_text')}
        primaryLabel={t('change_password.done')}
        onPrimaryClick={onClose}
        onClose={onClose}
      />
    );
  }

  return (
    <AuthMessageCard
      title={t('change_password.title')}
      text={t('change_password.subtitle')}
      onClose={onClose}
    >
      <AuthModalForm
        onSubmit={handleSubmit}
        submitLabel={t('change_password.submit')}
        isSubmitting={isLoading}
        error={formError}
      >
        <AuthField
          name="old_password"
          type="password"
          label={t('change_password.old_password')}
          value={oldPassword}
          onChange={setOldPassword}
          error={fieldErrors.old_password}
          autoComplete="current-password"
        />
        <AuthField
          name="new_password"
          type="password"
          label={t('change_password.new_password')}
          value={newPassword}
          onChange={setNewPassword}
          error={fieldErrors.new_password}
          autoComplete="new-password"
        />
        <AuthField
          name="new_password_confirm"
          type="password"
          label={t('change_password.new_password_confirm')}
          value={newPasswordConfirm}
          onChange={setNewPasswordConfirm}
          error={fieldErrors.new_password_confirm}
          autoComplete="new-password"
        />
      </AuthModalForm>
    </AuthMessageCard>
  );
};