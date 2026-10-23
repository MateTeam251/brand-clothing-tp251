import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { SearchSelect } from '../SearchSelect';
import {
  useGetDeliveryBranchesQuery,
  useGetDeliveryCitiesQuery,
} from '../../shared/api/deliveryApi';
import { useDebounce } from '../../shared/hooks/useDebounce';
import { CHECKOUT_DELIVERY_PROVIDER } from '../../shared/types/delivery';
import type {
  CheckoutDeliveryErrors,
  CheckoutDeliveryValues,
} from '../../shared/types/checkout';
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
      onChange({ city: null, branch: null });
    }
  };

  const handleCitySelect = (id: number) => {
    const city = cities.find((item) => item.id === id);

    if (!city) {
      return;
    }

    setCityQuery(city.name);
    setBranchQuery('');
    onChange({ city, branch: null });
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
      <p className={styles.delivery__carrier}>{t('checkout_delivery.carrier')}</p>

      <div className={styles.delivery__fields}>
        <SearchSelect
          label={t('checkout_delivery.city')}
          placeholder={t('checkout_delivery.city_placeholder')}
          value={cityQuery}
          onInputChange={handleCityInput}
          onSelect={handleCitySelect}
          options={cities.map((city) => ({ id: city.id, label: city.name }))}
          message={cityMessage}
          error={errors?.city}
        />

        <SearchSelect
          label={t('checkout_delivery.branch')}
          placeholder={t('checkout_delivery.branch_placeholder')}
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
      </div>
    </section>
  );
}