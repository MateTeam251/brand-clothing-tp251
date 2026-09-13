export interface ProductImage {
  id: number;
  image: string;
  order: number;
  color: string | null;
}

export interface ProductListItem {
  id: number;
  name: string;
  main_image: ProductImage | null;
  price_uah: string;
  price_usd: string;
  is_available: boolean;
  discounted_price_uah: string;
  discounted_price_usd: string;
  is_bestseller: boolean;
  is_new_collection: boolean;
}

export interface ProductColor {
  colors: {
    name: string;
    hex_code: string;
  };
  is_available: boolean;
}

export interface SizeGuide {
  id: number;
  product_type: string;
  image: string;
  description: string;
}

export interface ProductDetails {
  id: number;
  name: string;
  type: string;
  description: string;
  price_uah: string;
  price_usd: string;
  discounted_price_uah: string;
  discounted_price_usd: string;
  is_bestseller: boolean;
  images: ProductImage[];
  available_colors: ProductColor[];
  is_available: boolean;
  size_guide: SizeGuide;
}

export interface ProductQueryParams {
  lang?: string;
  currency?: string;
  collections?: string;
  search?: string;
  ordering?: string;
  page?: number;
}