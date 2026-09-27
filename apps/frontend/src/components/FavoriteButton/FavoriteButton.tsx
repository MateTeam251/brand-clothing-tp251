import { useState } from 'react';
import favouriteIcon from '../../shared/assets/icons/favourite.svg';
import favouriteHoveredIcon from '../../shared/assets/icons/favourite-hovered.svg';
import styles from './FavoriteButton.module.scss';

interface FavoriteButtonProps {
  isActive: boolean;
  onClick: () => void;
  ariaLabel: string;
}

export const FavoriteButton = ({ isActive, onClick, ariaLabel }: FavoriteButtonProps) => {
  const [isHovered, setIsHovered] = useState(false);
  const showActiveIcon = isHovered || isActive;

  return (
    <button
      type="button"
      className={styles.favoriteButton}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      aria-label={ariaLabel}
    >
      <span className={styles.favoriteButton__circle}>
        <img
          src={showActiveIcon ? favouriteHoveredIcon : favouriteIcon}
          alt=""
          className={styles.favoriteButton__icon}
        />
      </span>
    </button>
  );
};