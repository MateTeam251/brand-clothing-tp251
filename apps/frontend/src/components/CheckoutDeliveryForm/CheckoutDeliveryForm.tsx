import { SearchSelect } from '../SearchSelect';
import { AuthField } from '../AuthField';
import {
  useGetDeliveryBranchesQuery,
  useGetDeliveryCitiesQuery,
  useGetNovaPostCountriesQuery,
} from '../../shared/api/deliveryApi';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import { useDebounce } from '../../shared/hooks/useDebounce';
import { CHECKOUT_DELIVERY_PROVIDER, type NovaPostCountry } from '../../shared/types/delivery';
import type {
  CheckoutDeliveryErrors,
  CheckoutDeliveryValues,
  DeliveryMode,
  InternationalDeliveryValues,
} from '../../shared/types/checkout';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import styles from './CheckoutDeliveryForm.module.scss';

const MIN_CITY_LENGTH = 2;
const DEBOUNCE_MS = 300;

interface CheckoutDeliveryFormProps {
  value: CheckoutDeliveryValues;
  errors?: CheckoutDeliveryErrors;
  onChange: (value: CheckoutDeliveryValues) => void;
}

export function CheckoutDeliveryForm({
  value,
  errors,
  onChange,
}: CheckoutDeliveryFormProps) {
  const { t } = useTranslation();

  const [cityQuery, setCityQuery] = useState(value.city?.name ?? '');
  const [branchQuery, setBranchQuery] = useState(value.branch?.name ?? '');

  const trimmedCity = cityQuery.trim();
  const trimmedBranch = branchQuery.trim();
  const debouncedCity = useDebounce(trimmedCity, DEBOUNCE_MS);
  const debouncedBranch = useDebounce(trimmedBranch, DEBOUNCE_MS);

  // ---------- Режим доставки та країна ----------
  const language = useAppSelector((state) => state.settings.language);
  const [countryQuery, setCountryQuery] = useState(value.international.countryName);

  const {
    data: countries = [],
    isFetching: isCountriesFetching,
    isError: isCountriesError,
  } = useGetNovaPostCountriesQuery(undefined, { skip: value.mode !== 'international' });

  const getCountryName = (country: NovaPostCountry) =>
    language === 'ua' ? country.name_ua : country.name_en;

  const countryOptions = countries
    .map((country, index) => ({ id: index, label: getCountryName(country) }))
    .filter(
      (option) =>
        value.international.country ||
        option.label.toLowerCase().includes(countryQuery.trim().toLowerCase()),
    );

  let countryMessage: string | undefined;
  if (isCountriesFetching) {
    countryMessage = t('checkout_delivery.loading');
  } else if (isCountriesError) {
    countryMessage = t('checkout_delivery.load_error');
  } else if (!value.international.country && countryOptions.length === 0) {
    countryMessage = t('checkout_delivery.not_found');
  }

  const handleModeChange = (mode: DeliveryMode) => {
    if (mode !== value.mode) {
      onChange({ ...value, mode });
    }
  };

  const updateInternational = (patch: Partial<InternationalDeliveryValues>) => {
    onChange({ ...value, international: { ...value.international, ...patch } });
  };

  const handleCountryInput = (text: string) => {
    setCountryQuery(text);

    if (value.international.country) {
      updateInternational({ country: '', countryName: '' });
    }
  };

  const handleCountrySelect = (id: number) => {
    const country = countries[id];

    if (!country) {
      return;
    }

    setCountryQuery(getCountryName(country));
    updateInternational({ country: country.code, countryName: country.name_ua });
  };

  // ---------- Місто ----------
  const canSearchCity = !value.city && debouncedCity.length >= MIN_CITY_LENGTH;

  const {
    data: citiesData,
    isFetching: isCitiesFetching,
    isError: isCitiesError,
  } = useGetDeliveryCitiesQuery(
    { provider: CHECKOUT_DELIVERY_PROVIDER, search: debouncedCity },
    { skip: !canSearchCity },
  );

  const cities = canSearchCity ? (citiesData?.results ?? []) : [];

  let cityMessage: string | undefined;
  if (value.city) {
    cityMessage = undefined;
  } else if (trimmedCity.length < MIN_CITY_LENGTH) {
    cityMessage = t('checkout_delivery.city_hint');
  } else if (trimmedCity !== debouncedCity || isCitiesFetching) {
    cityMessage = t('checkout_delivery.loading');
  } else if (isCitiesError) {
    cityMessage = t('checkout_delivery.load_error');
  } else if (cities.length === 0) {
    cityMessage = t('checkout_delivery.not_found');
  }

  const handleCityInput = (text: string) => {
    setCityQuery(text);
    setBranchQuery('');

    if (value.city || value.branch) {
      onChange({ ...value, city: null, branch: null });
    }
  };

  const handleCitySelect = (id: number) => {
    const city = cities.find((item) => item.id === id);

    if (!city) {
      return;
    }

    setCityQuery(city.name);
    setBranchQuery('');
    onChange({ ...value, city, branch: null });
  };

  // ---------- Відділення ----------
  const cityId = value.city?.id;
  const branchSearch = value.branch ? '' : debouncedBranch;

  const {
    data: branchesData,
    isFetching: isBranchesFetching,
    isError: isBranchesError,
  } = useGetDeliveryBranchesQuery(
    { city: cityId ?? 0, search: branchSearch },
    { skip: !cityId },
  );

  const branches = cityId ? (branchesData?.results ?? []) : [];

  const isBranchTyping = !value.branch && trimmedBranch !== debouncedBranch;

  let branchMessage: string | undefined;
  if (!cityId) {
    branchMessage = t('checkout_delivery.select_city_first');
  } else if (isBranchTyping || isBranchesFetching) {
    branchMessage = t('checkout_delivery.loading');
  } else if (isBranchesError) {
    branchMessage = t('checkout_delivery.load_error');
  } else if (branches.length === 0) {
    branchMessage = t('checkout_delivery.not_found');
  }

  const handleBranchInput = (text: string) => {
    setBranchQuery(text);

    if (value.branch) {
      onChange({ ...value, branch: null });
    }
  };

  const handleBranchSelect = (id: number) => {
    const branch = branches.find((item) => item.id === id);

    if (!branch) {
      return;
    }

    setBranchQuery(branch.name);
    onChange({ ...value, branch });
  };

  return (
    <section className={styles.delivery}>
      <h2 className={styles.delivery__title}>{t('checkout_delivery.title')}</h2>

      <div
        className={styles.delivery__modes}
        role="radiogroup"
        aria-label={t('checkout_delivery.title')}
      >
        <label className={styles.delivery__mode}>
          <input
            type="radio"
            name="delivery-mode"
            checked={value.mode === 'ukraine'}
            onChange={() => handleModeChange('ukraine')}
          />
          <span>{t('checkout_delivery.mode_ukraine')}</span>
        </label>

        <label className={styles.delivery__mode}>
          <input
            type="radio"
            name="delivery-mode"
            checked={value.mode === 'international'}
            onChange={() => handleModeChange('international')}
          />
          <span>{t('checkout_delivery.mode_international')}</span>
        </label>
      </div>

      <div className={styles.delivery__fields}>
        {value.mode === 'ukraine' ? (
          <>
            <div className={styles.delivery__method}>{t('checkout_delivery.method')}</div>

            <SearchSelect
              label={t('checkout_delivery.city')}
              placeholder={t('checkout_delivery.city')}
              value={cityQuery}
              onInputChange={handleCityInput}
              onSelect={handleCitySelect}
              options={cities.map((city) => ({ id: city.id, label: city.name }))}
              message={cityMessage}
              error={errors?.city}
            />

            <SearchSelect
              label={t('checkout_delivery.branch')}
              placeholder={t('checkout_delivery.branch')}
              value={branchQuery}
              onInputChange={handleBranchInput}
              onSelect={handleBranchSelect}
              options={branches.map((branch) => ({
                id: branch.id,
                label: branch.name,
                description: branch.address,
              }))}
              message={branchMessage}
              disabled={!cityId}
              error={errors?.branch}
            />
          </>
        ) : (
          <>
            <div className={styles.delivery__method}>
              {t('checkout_delivery.method_international')}
            </div>

            <SearchSelect
              label={t('checkout_delivery.country')}
              placeholder={t('checkout_delivery.country')}
              value={countryQuery}
              onInputChange={handleCountryInput}
              onSelect={handleCountrySelect}
              options={countryOptions}
              message={countryMessage}
              error={errors?.country}
            />

            <AuthField
              name="delivery-region"
              label={t('checkout_delivery.region')}
              value={value.international.region}
              onChange={(region) => updateInternational({ region })}
              autoComplete="address-level1"
            />

            <AuthField
              name="delivery-city"
              label={t('checkout_delivery.city')}
              value={value.international.city}
              onChange={(city) => updateInternational({ city })}
              error={errors?.internationalCity}
              autoComplete="address-level2"
            />

            <AuthField
              name="delivery-address"
              label={t('checkout_delivery.address')}
              value={value.international.address}
              onChange={(address) => updateInternational({ address })}
              error={errors?.address}
              autoComplete="address-line1"
            />

            <AuthField
              name="delivery-house-number"
              label={t('checkout_delivery.house_number')}
              value={value.international.houseNumber}
              onChange={(houseNumber) => updateInternational({ houseNumber })}
              error={errors?.houseNumber}
            />

            <AuthField
              name="delivery-apartment"
              label={t('checkout_delivery.apartment')}
              value={value.international.apartment}
              onChange={(apartment) => updateInternational({ apartment })}
              autoComplete="address-line2"
            />

            <AuthField
              name="delivery-postal-code"
              label={t('checkout_delivery.postal_code')}
              value={value.international.postalCode}
              onChange={(postalCode) => updateInternational({ postalCode })}
              error={errors?.postalCode}
              autoComplete="postal-code"
            />
          </>
        )}
      </div>
    </section>
  );
}
