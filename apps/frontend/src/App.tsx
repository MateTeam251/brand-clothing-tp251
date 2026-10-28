import { Routes, Route, BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './app/store/store';
import './app/styles/styles.scss';
import { HomePage } from './pages/HomePage';
import { AccountPage} from './pages/AccountPage';
import { FavoritesPage } from './pages/FavoritesPage';
import { CatalogPage } from './pages/CatalogPage';
import { CartPage } from './pages/CartPage';
import { CheckoutPage } from './pages/CheckoutPage';
import { PasswordResetPage } from './pages/PasswordResetPage';
import { PasswordForgotPage } from './pages/PasswordForgotPage';
import { AboutPage } from './pages/AboutPage';
import { GarmentCarePage } from './pages/GarmentCarePage';
import { OrderConfirmationPage } from './pages/OrderConfirmationPage';
import { ProductDetailsPage } from './pages/ProductDetailsPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { SignInPage } from './pages/SignInPage';
import { SignUpPage } from './pages/SignUpPage';
import { Header } from './components/Layout/Header';
import { Footer } from './components/Layout/Footer';
import { ScrollToTop } from './components/ScrollToTop';
import { ProtectedRoute } from './components/ProtectedRoute';
import { ActivationSuccessPage } from './pages/ActivationSuccessPage';
import { ActivationFailedPage } from './pages/ActivationFailedPage';
import { DeliveryPage } from './pages/DeliveryPage';
import { ReturnsPage } from './pages/ReturnsPage';
import { PrivacyPage } from './pages/PrivacyPage';
import { EmailChangeSuccessPage } from './pages/EmailChangeSuccessPage';
import { EmailChangeFailedPage } from './pages/EmailChangeFailedPage';


function App() {
  return (
    <Provider store={store}>
      <BrowserRouter>
        <div className="app-shell">
          <Header />

          <main className="app-shell__content">
            <ScrollToTop />
            <Routes>
              <Route path='/' element={<HomePage />} />
              <Route path='/catalog' element={<CatalogPage />} />
              <Route path='/product/:id' element={<ProductDetailsPage />} />
              <Route path='/cart' element={<CartPage />} />
              <Route path='/checkout' element={<CheckoutPage />} />
              <Route path='/confirmation' element={<OrderConfirmationPage />} />
              <Route path='/about' element={<AboutPage />} />
              <Route path='/garment-care' element={<GarmentCarePage />} />
              <Route path='/delivery' element={<DeliveryPage />} />
              <Route path='/returns' element={<ReturnsPage />} />
              <Route path='/privacy' element={<PrivacyPage />} />
              <Route path='/forgotpassword' element={<PasswordForgotPage />} />
              <Route path='/resetpassword' element={<PasswordResetPage />} />
              <Route path='/signin' element={<SignInPage />} />
              <Route path='/signup' element={<SignUpPage />} />
              <Route path='/activation/success' element={<ActivationSuccessPage />} />
              <Route path='/activation/failed' element={<ActivationFailedPage />} />
              <Route path='/email-change/success' element={<EmailChangeSuccessPage />} />
              <Route path='/email-change/failed' element={<EmailChangeFailedPage />} />

              <Route element={<ProtectedRoute />}>
                <Route path="/account" element={<AccountPage />} />
                <Route path="/favorites" element={<FavoritesPage />} />
              </Route>

              <Route path='*' element={<NotFoundPage />} />
            </Routes>
          </main>

          <Footer />
        </div>
      </BrowserRouter>
    </Provider>
  );
}

export default App;
