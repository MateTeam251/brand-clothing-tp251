import type { ProductListItem } from './products';

export interface FavoriteItem {
  id: number;
  product: number;
  product_details: ProductListItem;
  created_at: string;
}

export interface AddFavoriteRequest {
  product: number;
}