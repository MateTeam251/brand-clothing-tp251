import { useState } from 'react';
import type { ProductImage } from '../../shared/types/products';
import styles from './ProductGallery.module.scss';

interface ProductGalleryProps {
  images: ProductImage[];
  alt: string;
}

export const ProductGallery = ({ images, alt }: ProductGalleryProps) => {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const touchStartX = useState(0);

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX[1](e.touches[0].clientX);
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    const touchEndX = e.changedTouches[0].clientX;
    const diff = touchStartX[0] - touchEndX;

    if (Math.abs(diff) < 50) {
      return;
    }

    if (diff > 0 && selectedIndex < images.length - 1) {
      setSelectedIndex((prev) => prev + 1);
    } else if (diff < 0 && selectedIndex > 0) {
      setSelectedIndex((prev) => prev - 1);
    }
  };

  return (
    <div className={styles.gallery}>
      <div className={styles.gallery__thumbnails}>
        {images.map((image, index) => (
          <button
            key={image.id}
            type="button"
            className={`${styles.gallery__thumbnail} ${
              index === selectedIndex ? styles['gallery__thumbnail--active'] : ''
            }`}
            onClick={() => setSelectedIndex(index)}
          >
            <img src={image.image} alt="" />
          </button>
        ))}
      </div>

      <div
        className={styles.gallery__mainImage}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        {images[selectedIndex] ? (
          <img src={images[selectedIndex].image} alt={alt} />
        ) : (
          <div className={styles.gallery__imagePlaceholder} />
        )}

        <div className={styles.gallery__dots}>
          {images.map((_, index) => (
            <span
              key={index}
              className={`${styles.gallery__dot} ${
                index === selectedIndex ? styles['gallery__dot--active'] : ''
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
};