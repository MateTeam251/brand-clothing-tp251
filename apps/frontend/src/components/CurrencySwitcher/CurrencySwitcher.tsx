import { useAppDispatch, useAppSelector } from '../../shared/hooks/reduxHooks';
import { setCurrency } from '../../app/store/reducers/settingsSlice';
import styles from './CurrencySwitcher.module.scss';

export const CurrencySwitcher = () => {
  const dispatch = useAppDispatch();
  const currency = useAppSelector((state) => state.settings.currency);

  return (
    <div className={styles.switcher}>
      <button
        type="button"
        className={styles.switcher__button}
        onClick={() => dispatch(setCurrency('uah'))}
        aria-pressed={currency === 'uah'}
      >
        UAH
      </button>
      <div className={styles.switcher__divider} />
      <button
        type="button"
        className={styles.switcher__button}
        onClick={() => dispatch(setCurrency('usd'))}
        aria-pressed={currency === 'usd'}
      >
        USD
      </button>
    </div>
  );
};