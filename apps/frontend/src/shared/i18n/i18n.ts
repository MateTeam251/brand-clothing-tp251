import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

i18n.use(initReactI18next).init({
  lng: localStorage.getItem('language') ?? 'en', 
  fallbackLng: 'en',
  react: {
    useSuspense: false,
  },
  resources: {
    en: {
      translation: {
        catalog: 'Catalog',
        about: 'About Us',
        instagram: 'Instagram',
        care: 'Care',
        delivery: 'Delivery',
        refund: "Refund's",
        privacy: 'Privacy policy'
      }
    }, 
    ua: {
      translation: {
        catalog: 'Каталог',
        about: 'Про нас',
        instagram: 'Інстаграм',
        care: 'Догляд',
        delivery: 'Доставка',
        refund: 'Повернненя',
        privacy: 'Політика конфіденційності'
      }
    }
  }
});

export default i18n;