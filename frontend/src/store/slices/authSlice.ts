import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Currency } from '../../types';

interface AuthState {
  token: string | null;
  email: string | null;
  role: string | null;
  merchantId: string | null;
  activePortal: 'MERCHANT' | 'ADMIN';
  selectedCurrency: Currency;
}

const initialState: AuthState = {
  // Pre-seed demo token or read from localStorage
  token: localStorage.getItem('castor_token') || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
  email: localStorage.getItem('castor_email') || 'demo@castorpay.dev',
  role: localStorage.getItem('castor_role') || 'MERCHANT_ADMIN',
  merchantId: localStorage.getItem('castor_merchant_id') || 'e4cab755-d192-4fa8-9212-4ce9c2df768e',
  activePortal: 'MERCHANT',
  selectedCurrency: 'NGN',
};

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (
      state,
      action: PayloadAction<{ token: string; email: string; role?: string; merchantId?: string }>
    ) => {
      state.token = action.payload.token;
      state.email = action.payload.email;
      if (action.payload.role) {
        state.role = action.payload.role;
        localStorage.setItem('castor_role', action.payload.role);
        // Automatically switch portal view if admin
        if (action.payload.role === 'ADMIN' || action.payload.role === 'TREASURY') {
          state.activePortal = 'ADMIN';
        } else {
          state.activePortal = 'MERCHANT';
        }
      }
      if (action.payload.merchantId) {
        state.merchantId = action.payload.merchantId;
        localStorage.setItem('castor_merchant_id', action.payload.merchantId);
      }
      localStorage.setItem('castor_token', action.payload.token);
      localStorage.setItem('castor_email', action.payload.email);
    },
    logout: (state) => {
      state.token = null;
      state.email = null;
      state.role = null;
      state.merchantId = null;
      localStorage.removeItem('castor_token');
      localStorage.removeItem('castor_email');
      localStorage.removeItem('castor_role');
      localStorage.removeItem('castor_merchant_id');
    },
    setActivePortal: (state, action: PayloadAction<'MERCHANT' | 'ADMIN'>) => {
      state.activePortal = action.payload;
    },
    setSelectedCurrency: (state, action: PayloadAction<Currency>) => {
      state.selectedCurrency = action.payload;
    },
  },
});

export const { setCredentials, logout, setActivePortal, setSelectedCurrency } = authSlice.actions;
export default authSlice.reducer;
