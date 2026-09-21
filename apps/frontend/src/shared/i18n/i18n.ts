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
        privacy: 'Privacy policy',
        'autumn-collection': 'Autumn collection',
        bestsellers: 'Our bestsellers',
        'new-collections': 'New collections',
        'view-all': 'View all',
        'search-placeholder': 'Search in catalog...',
        'subscribe-title': 'A personality that needs no explanation',
        'subscribe-subtitle': 'We create clothes that speak for you without words. Be the first to know about new releases and exclusive sales!',
        'collections': 'Collections',
        cart: 'Cart',
        'empty-cart': 'Your cart is empty.',
        total: 'Total',
        'cart-delivery': 'Payment at check-out',
        products: 'Products',
        'cart-item-desc': '5–8 days for custom orders',
        size: 'Size'
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
        privacy: 'Політика конфіденційності',
        'autumn-collection': 'Осіння колекція',
        bestsellers: 'Наші бестселери',
        'new-collections': 'Нові колекції',
        'view-all': 'Переглянути все',
        'search-placeholder': 'Пошук в каталозі...',
        'subscribe-title': 'Індивідуальність, що не потребує пояснень',
        'subscribe-subtitle': 'Створюємо одяг, що говорить про тебе без слів. Будь першою у курсі нових релізів та закритих сейлів!',
        'collections': 'Колекції',
        cart: 'Кошик',
        'empty-cart': 'Ваш кошик порожній.',
        total: 'Разом',
        'cart-delivery': 'Розрахунок при оформленні',
        products: 'Товари',
        'cart-item-desc': 'Під замовлення 5-8 днів',
        size: 'Розмір'
      }
    }
  }
});

export default i18n;