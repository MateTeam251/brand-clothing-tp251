import { useState } from 'react';
import type { SyntheticEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useUpdateMeMutation } from '../../shared/api/userApi';
import type { UserProfile } from '../../shared/types/User';
import { AuthField } from '../AuthField';
import { ChangeEmailModal } from '../ChangeEmailModal';
import { ChangePasswordModal } from '../ChangePasswordModal';
import styles from './ProfileForm.module.scss';

interface ProfileFormProps {
  profile: UserProfile;
}

export const ProfileForm = ({ profile }: ProfileFormProps) => {
  const { t } = useTranslation();
  const [updateMe, { isLoading }] = useUpdateMeMutation();
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const [isEmailModalOpen, setIsEmailModalOpen] = useState(false);

  const [firstName, setFirstName] = useState(profile.first_name ?? '');
  const [lastName, setLastName] = useState(profile.last_name ?? '');
  const [birthDate, setBirthDate] = useState(profile.birth_date ?? '');
  const [phone, setPhone] = useState(profile.phone_number ?? '');
  const [instagram, setInstagram] = useState(profile.instagram ?? '');
  const [telegram, setTelegram] = useState(profile.telegram ?? '');
  const [marketingOptIn, setMarketingOptIn] = useState(profile.marketing_opt_in);
  const [errors, setErrors] = useState<{
    firstName?: string;
    lastName?: string;
    phone?: string;
  }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSaved, setIsSaved] = useState(false);

  const handleChange = (setter: (value: string) => void) => (value: string) => {
    setter(value);
    setIsSaved(false);
    setFormError(null);
  };

  const handleChangePassword = () => {
    setIsPasswordModalOpen(true);
  };

  const handleSubmit = async (event: SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextErrors = {
      firstName: firstName.trim() ? undefined : t('profile.errors.first_name_required'),
      lastName: lastName.trim() ? undefined : t('profile.errors.last_name_required'),
      phone: phone.trim() ? undefined : t('profile.errors.phone_required'),
    };

    setErrors(nextErrors);

    if (nextErrors.firstName || nextErrors.lastName || nextErrors.phone) {
      return;
    }

    setFormError(null);

    try {
      await updateMe({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        birth_date: birthDate || null,
        phone_number: phone.trim(),
        instagram: instagram.trim(),
        telegram: telegram.trim(),
        marketing_opt_in: marketingOptIn,
      }).unwrap();
      setIsSaved(true);
    } catch {
      setFormError(t('profile.errors.save_failed'));
    }
  };

  return (
    <>
      <form className={styles.form} onSubmit={handleSubmit} noValidate>
        <div className={styles.form__fields}>
          <AuthField
            name="profile-first-name"
            label={t('profile.first_name')}
            value={firstName}
            onChange={handleChange(setFirstName)}
            autoComplete="given-name"
            error={errors.firstName}
          />
          <AuthField
            name="profile-last-name"
            label={t('profile.last_name')}
            value={lastName}
            onChange={handleChange(setLastName)}
            autoComplete="family-name"
            error={errors.lastName}
          />
          <AuthField
            name="profile-birth-date"
            type="date"
            label={t('profile.birth_date')}
            value={birthDate}
            onChange={handleChange(setBirthDate)}
            autoComplete="bday"
          />
          <AuthField
            name="profile-phone"
            type="tel"
            label={t('profile.phone')}
            value={phone}
            onChange={handleChange(setPhone)}
            autoComplete="tel"
            error={errors.phone}
          />
          <AuthField
            name="profile-instagram"
            label={t('profile.instagram')}
            value={instagram}
            onChange={handleChange(setInstagram)}
          />
          <AuthField
            name="profile-telegram"
            label={t('profile.telegram')}
            value={telegram}
            onChange={handleChange(setTelegram)}
          />
          <AuthField
            name="profile-email"
            type="email"
            label={t('profile.email')}
            value={profile.email}
            disabled
          />
        </div>

        <button
          type="button"
          className={styles.form__changePassword}
          onClick={() => setIsEmailModalOpen(true)}
        >
          {t('profile.change_email')}
        </button>

        <button type="button" className={styles.form__changePassword} onClick={handleChangePassword}>
          {t('profile.change_password')}
        </button>

        <label className={styles.form__checkbox}>
          <input
            type="checkbox"
            checked={marketingOptIn}
            onChange={(event) => {
              setMarketingOptIn(event.target.checked);
              setIsSaved(false);
            }}
          />
          <span>{t('profile.marketing')}</span>
        </label>

        {formError && (
          <p className={styles.form__error} role="alert">
            {formError}
          </p>
        )}
        {isSaved && (
          <p className={styles.form__success} role="status">
            {t('profile.saved')}
          </p>
        )}

        <button type="submit" className={styles.form__submit} disabled={isLoading}>
          {t('profile.save')}
        </button>
      </form>

    {isPasswordModalOpen && (
      <ChangePasswordModal onClose={() => setIsPasswordModalOpen(false)} />
    )}
      
    {isEmailModalOpen && (
      <ChangeEmailModal
        currentEmail={profile.email}
        onClose={() => setIsEmailModalOpen(false)}
      />
    )}
    </>
  );
};