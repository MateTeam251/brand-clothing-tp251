declare global {
  interface Window {
    dataLayer: unknown[];
    gtag?: (...args: unknown[]) => void;
  }
}

export type AnalyticsEventName =
  | 'view_item_list'
  | 'select_item'
  | 'view_item'
  | 'select_size'
  | 'add_to_cart'
  | 'view_cart'
  | 'remove_from_cart'
  | 'begin_checkout'
  | 'add_shipping_info'
  | 'add_payment_info'
  | 'login'
  | 'sign_up';

type AnalyticsParams = Record<string, unknown>;

const MEASUREMENT_ID = import.meta.env.VITE_GA_MEASUREMENT_ID as string | undefined;

export const initAnalytics = () => {
  if (!MEASUREMENT_ID || window.gtag) {
    return;
  }

  window.dataLayer = window.dataLayer || [];
  window.gtag = function gtag() {
    // eslint-disable-next-line prefer-rest-params
    window.dataLayer.push(arguments);
  };

  window.gtag('js', new Date());
  window.gtag('config', MEASUREMENT_ID);

  const script = document.createElement('script');

  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${MEASUREMENT_ID}`;
  document.head.appendChild(script);
};

export const trackEvent = (name: AnalyticsEventName, params?: AnalyticsParams) => {
  if (!MEASUREMENT_ID || !window.gtag) {
    return;
  }

  window.gtag('event', name, params);
};

export interface AnalyticsItem {
  item_id: string;
  item_name: string;
  price: number;
  item_variant?: string;
  item_list_name?: string;
  index?: number;
  quantity?: number;
}

interface AnalyticsProduct {
  id: number;
  name: string;
  price: string;
  discounted_price: string | null;
}

export const toAnalyticsItem = (
  product: AnalyticsProduct,
  extra?: Partial<AnalyticsItem>,
): AnalyticsItem => ({
  item_id: String(product.id),
  item_name: product.name,
  price: Number(product.discounted_price ?? product.price),
  ...extra,
});

interface AnalyticsCartLine {
  product: number;
  name: string;
  size: string;
  quantity: number;
  price: string;
}

export const cartLineToAnalyticsItem = (line: AnalyticsCartLine): AnalyticsItem => ({
  item_id: String(line.product),
  item_name: line.name,
  price: Number(line.price),
  item_variant: line.size,
  quantity: line.quantity,
});

export const setAnalyticsUserId = (userId: number | string | null) => {
  if (!MEASUREMENT_ID || !window.gtag) {
    return;
  }

  window.gtag('set', { user_id: userId === null ? null : String(userId) });
};