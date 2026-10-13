import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title?: string;
  message: string;
}

interface UIState {
  toasts: Toast[];
  activeModal: string | null;
}

const initialState: UIState = {
  toasts: [],
  activeModal: null,
};

export const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    addToast: (state, action: PayloadAction<Omit<Toast, 'id'>>) => {
      const id = `${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      state.toasts.push({
        ...action.payload,
        id,
      });
    },
    removeToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter((t) => t.id !== action.payload);
    },
    clearToasts: (state) => {
      state.toasts = [];
    },
    setActiveModal: (state, action: PayloadAction<string | null>) => {
      state.activeModal = action.payload;
    },
  },
});

export const { addToast, removeToast, clearToasts, setActiveModal } = uiSlice.actions;
export default uiSlice.reducer;
