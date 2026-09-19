import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

export type Language = 'ua' | 'en';
export type Currency = 'uah' | 'usd';

interface SettingsState {
  language: Language;
  currency: Currency;
}

const initialState: SettingsState = {
  language: (localStorage.getItem('language') as Language | null) ?? 'en',
  currency: (localStorage.getItem('currency') as Currency | null) ?? 'usd',
};

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    setLanguage: (state, action: PayloadAction<Language>) => {
      state.language = action.payload;
      localStorage.setItem('language', action.payload);
    },
    setCurrency: (state, action: PayloadAction<Currency>) => {
      state.currency = action.payload;
      localStorage.setItem('currency', action.payload);
    },
  },
});

export const { setLanguage, setCurrency } = settingsSlice.actions;
export default settingsSlice.reducer;
