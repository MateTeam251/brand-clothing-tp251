import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useGetProductByIdQuery } from '../../shared/api/productsApi';
import { useAddFavoriteMutation, useRemoveFavoriteByProductIdMutation } from '../../shared/api/favoritesApi';
import { useAppSelector, useAppDispatch } from '../../shared/hooks/reduxHooks';
import { addToCart } from '../../app/store/reducers/cartSlice';
import { SIZES } from '../../shared/types/common';
import { Loader } from '../../components/Loader/Loader';
import { ErrorState } from '../../components/ErrorState/ErrorState';
import { ProductSlider } from '../../components/Product/ProductSlider';
import { AvailabilityRequestForm } from '../../components/AvailabilityRequestForm/AvailabilityRequestForm';
import plusIcon from '../../shared/assets/icons/plus.svg';
import minusIcon from '../../shared/assets/icons/minus.svg';
import styles from './ProductDetailsPage.module.scss';
import { ProductGallery } from '../../components/ProductGallery';
import { FavoriteButton } from '../../components/FavoriteButton';

export const ProductDetailsPage = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { currency, language } = useAppSelector((state) => state.settings);
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);
  const [selectedSize, setSelectedSize] = useState('');
  const [isAvailabilityFormOpen, setIsAvailabilityFormOpen] = useState(false);
  const [isSizeGuideOpen, setIsSizeGuideOpen] = useState(false);

  const { data: product, isLoading, error } = useGetProductByIdQuery({
    id: Number(id),
    currency,
    lang: language,
  });

  const [addFavorite] = useAddFavoriteMutation();
  const [removeFavorite] = useRemoveFavoriteByProductIdMutation();

  if (isLoading) {
    return <Loader />;
  }

  if (error || !product) {
    return <ErrorState />;
  }

  const formatPrice = (price: string) =>
    new Intl.NumberFormat(currency.toUpperCase() === 'UAH' ? 'uk-UA' : 'en-US', {
      style: 'currency',
      currency: currency.toUpperCase(),
      currencyDisplay: 'narrowSymbol',
      maximumFractionDigits: 0,
    }).format(Number(price));

  const displayedPrice = product.discounted_price ?? product.price;
  const hasDiscount = Boolean(product.discounted_price);

  const handleFavoriteClick = () => {
    if (!isAuthenticated) {
      navigate('/signin');
      return;
    }

    if (product.is_favorite) {
      removeFavorite(product.id);
    } else {
      addFavorite({ product: product.id });
    }
  };

  const handleAddToCart = () => {
    if (!selectedSize) {
      return;
    }

    dispatch(addToCart({
      id: Date.now(),
      product: product.id,
      size: selectedSize,
      quantity: 1,
    }));
  };

  return (
    <div className={styles.details}>
      <div className={styles.details__main}>
        <ProductGallery images={product.images} alt={product.name} />

        <div className={styles.details__info}>
          <div className={styles.details__block}>
            <div className={styles.details__top}>
              <div className={styles.details__header}>
                <h1 className={styles.details__name}>{product.name}</h1>

                <FavoriteButton
                  isActive={product.is_favorite}
                  onClick={handleFavoriteClick}
                  ariaLabel={t(product.is_favorite ? 'product.remove_favorite' : 'product.add_favorite')}
                />

                <div className={styles.details__prices}>
                  <span className={styles.details__price}>{formatPrice(displayedPrice)}</span>
                  {hasDiscount && (
                    <span className={styles.details__oldPrice}>{formatPrice(product.price)}</span>
                  )}
                </div>

                <p className={styles.details__shortDesc}>{product.description.split('\n')[0]}</p>
              </div>

              <div className={styles.details__sizeSelect}>
                <select
                  value={selectedSize}
                  onChange={(e) => setSelectedSize(e.target.value)}
                  className={styles.details__selector}
                >
                  <option value="">{t('product.select_size')}</option>
                  {SIZES.map((size) => (
                    <option key={size} value={size}>{size}</option>
                  ))}
                </select>
              </div>

              <div className={styles.details__guide}>
                {product.size_guide.image && (
                  <button
                    type="button"
                    className={styles.details__sizeGuideLink}
                    onClick={() => setIsSizeGuideOpen((prev) => !prev)}
                  >
                    {t('product.size')}
                  </button>
                )}

                {isSizeGuideOpen && product.size_guide.image && (
                  <div className={styles.details__sizeGuideOverlay} onClick={() => setIsSizeGuideOpen(false)}>
                    <img
                      src={product.size_guide.image}
                      alt={t('product.size')}
                      className={styles.details__sizeGuideImage}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                )}

                <p className={styles.details__delivery}>{t('cart_item_desc')}</p>
              </div>
              </div>

            <div className={styles.details__actions}>
              <div className={styles.details__addAction}>
                <button
                  type="button"
                  className={styles.details__addToCart}
                  onClick={handleAddToCart}
                  disabled={!selectedSize}
                >
                  {t('product.cart_btn')}
                </button>

                <p className={styles.details__note}>{t('product.addToCart_note')}</p>
              </div>

              <button
                type="button"
                className={styles.details__checkAvailability}
                onClick={() => setIsAvailabilityFormOpen((prev) => !prev)}
              >
                {t('product.check_availability')}
              </button>
            </div>

            {isAvailabilityFormOpen && <AvailabilityRequestForm productId={product.id} />}
          </div>

          <div className={styles.details__accordion}>
            {[
              { key: 'description_title', content: product.description },
              { key: 'material_title', content: product.fabric_composition },
              { key: 'care_title', content: t('care') },
              { key: 'delivery_title', content: t('delivery') },
            ].map((item) => (
              <details key={item.key} className={styles.details__accordionItem}>
                <summary className={styles.details__accordionSummary}>
                  <span className={styles.details__accordionTitle}>{t(`product.${item.key}`)}</span>
                  <span className={styles.details__accordionIconWrapper}>
                    <img src={plusIcon} alt="" className={styles.details__accordionIconPlus} />
                    <img src={minusIcon} alt="" className={styles.details__accordionIconMinus} />
                  </span>
                </summary>
                <p className={styles.details__accordionContent}>{item.content}</p>
              </details>
            ))}
          </div>
        </div>

        <div className={styles.details__recommended}>
          <ProductSlider
            title={t('product.slider_title')}
            queryParams={{ currency, lang: language }}
            showViewAll={false}
          />
        </div>
      </div>
    </div>
  );
};