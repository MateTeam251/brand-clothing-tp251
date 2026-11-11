import { useEffect } from 'react';
import { useAppSelector } from './reduxHooks';
import type { Language } from '../../app/store/reducers/settingsSlice';

const HTML_LANG: Record<Language, string> = {
  ua: 'uk',
  en: 'en',
};

export const useDocumentLanguage = () => {
  const language = useAppSelector((state) => state.settings.language);

  useEffect(() => {
    document.documentElement.lang = HTML_LANG[language];
  }, [language]);
};