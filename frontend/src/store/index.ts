import { configureStore } from '@reduxjs/toolkit';
import authSlice from './slices/authSlice';
import surveySlice from './slices/surveySlice';
import processingSlice from './slices/processingSlice';
import reportSlice from './slices/reportSlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    surveys: surveySlice,
    processing: processingSlice,
    reports: reportSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;