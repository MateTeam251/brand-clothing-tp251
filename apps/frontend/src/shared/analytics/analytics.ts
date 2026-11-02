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