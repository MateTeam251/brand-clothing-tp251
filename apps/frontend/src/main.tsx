import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './shared/i18n/i18n';
import { initAnalytics } from './shared/analytics';

import App from './App.tsx';

initAnalytics();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    
    <App />
  </StrictMode>
);
