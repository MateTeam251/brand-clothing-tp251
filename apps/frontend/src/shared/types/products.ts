export interface ProductImageColor {
  name: string;
  hex_code: string;
}

export interface ProductImage {
  id: number;
  image: string;
  order: number;
}

export interface Collection {
  id: number;
  slug: string;
  name: string;
  description: string;
}

export interface ProductListItem {
  id: number;
  name: string;
  collection: Collection;
  main_image: ProductImage | null;
  price: string;
  discounted_price: string | null;
  is_available: boolean;
  is_bestseller: boolean;
  is_new_collection: boolean;
  is_favorite: boolean;
}

export interface AvailableColor {
  colors: ProductImageColor;
  is_available: boolean;
}

export interface SizeGuide {
  image: string;
  description: string;
}

export interface ProductDetails {
  id: number;
  name: string;
  type: string;
  collection: Collection;
  description: string;
  fabric_composition: string;
  price: string;
  discounted_price: string | null;
  is_bestseller: boolean;
  images: ProductImage[];
  is_available: boolean;
  size_guide: SizeGuide;
  is_favorite: boolean;
}

export interface ProductQueryParams {
  lang?: string;
  currency?: string;
  collection?: string;
  type?: string;
  is_bestseller?: boolean;
  search?: string;
  ordering?: string;
  offset?: number;
  limit?: number;
}