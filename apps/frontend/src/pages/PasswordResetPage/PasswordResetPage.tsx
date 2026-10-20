import { useState } from 'react';
import type { SyntheticEvent } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useConfirmPasswordResetMutation } from '../../shared/api/authApi';
import { AuthField } from '../../components/AuthField';
import { AuthMessageCard } from '../../components/AuthMessageCard';
import { AuthModalForm } from '../../components/AuthModalForm';
import { useCloseAuth } from '../../shared/hooks/useCloseAuth';

type Status = 'form' | 'success' | 'invalid';

export const PasswordResetPage = () => {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const uid = searchParams.get('uid');
  const token = searchParams.get('token');
  const [confirmReset, { isLoading }] = useConfirmPasswordResetMutation();

  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{ password?: string; passwordConfirm?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>('form');
  const closeAuth = useCloseAuth();

  if (!uid || !token || status === 'invalid') {
    return (
      <AuthMessageCard
        variant="error"
        title={t('password_recovery.invalid_link.title')}
        text={t('password_recovery.invalid_link.text')}
        linkTo="/forgotpassword"
        linkLabel={t('password_recovery.invalid_link.request_new')}
        onClose={closeAuth}
      />
    );
  }

  if (status === 'success') {
    return (
      <AuthMessageCard
        variant="success"
        title={t('password_recovery.success.title')}
        text={t('password_recovery.success.text')}
        linkTo="/signin"
        linkLabel={t('password_recovery.success.sign_in')}
        onClose={closeAuth}
      />
    );
  }

  const handleSubmit = async (event: SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault();

    const errors: { password?: string; passwordConfirm?: string } = {};

    if (!password) {
      errors.password = t('auth.errors.required');
    }

    if (!passwordConfirm) {
      errors.passwordConfirm = t('auth.errors.required');
    } else if (password !== passwordConfirm) {
      errors.passwordConfirm = t('password_recovery.errors.password_mismatch');
    }

    setFieldErrors(errors);
    setFormError(null);

    if (Object.keys(errors).length > 0) {
      return;
    }

    try {
      await confirmReset({ uidb64: uid, token, new_password: password }).unwrap();
      setStatus('success');
    } catch (error) {
      const { status: httpStatus, data } = error as { status?: number; data?: unknown };

      if (httpStatus === 429) {
        setFormError(t('auth.errors.too_many_requests'));
        return;
      }

      const passwordErrors = (data as { new_password?: unknown } | undefined)?.new_password;

      if (httpStatus === 400 && Array.isArray(passwordErrors) && typeof passwordErrors[0] === 'string') {
        setFieldErrors({ password: passwordErrors[0] });
      } else if (httpStatus === 400) {
        setStatus('invalid');
      } else {
        setFormError(t('auth.errors.generic'));
      }
    }
  };

  return (
    <AuthMessageCard
      title={t('password_recovery.new_password.title')}
      onClose={closeAuth}
    >
      <AuthModalForm
        onSubmit={handleSubmit}
        submitLabel={t('password_recovery.new_password.submit')}
        isSubmitting={isLoading}
        error={formError}
      >
        <AuthField
          name="new_password"
          type="password"
          label={t('password_recovery.new_password.password')}
          value={password}
          onChange={setPassword}
          error={fieldErrors.password}
          autoComplete="new-password"
        />
        <AuthField
          name="new_password_confirm"
          type="password"
          label={t('password_recovery.new_password.confirm')}
          value={passwordConfirm}
          onChange={setPasswordConfirm}
          error={fieldErrors.passwordConfirm}
          autoComplete="new-password"
        />
      </AuthModalForm>
    </AuthMessageCard>
  );
};