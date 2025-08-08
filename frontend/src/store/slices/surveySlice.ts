import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Survey {
  id: string;
  name: string;
  description: string;
  survey_type: string;
  file_type: string;
  file_size: number;
  total_rows: number;
  total_columns: number;
  has_weights: boolean;
  weight_column?: string;
  created_at: string;
  updated_at: string;
}

interface SurveyState {
  surveys: Survey[];
  currentSurvey: Survey | null;
  isLoading: boolean;
  error: string | null;
  uploadProgress: number;
}

const initialState: SurveyState = {
  surveys: [],
  currentSurvey: null,
  isLoading: false,
  error: null,
  uploadProgress: 0,
};

const surveySlice = createSlice({
  name: 'surveys',
  initialState,
  reducers: {
    fetchSurveysStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    fetchSurveysSuccess: (state, action: PayloadAction<Survey[]>) => {
      state.surveys = action.payload;
      state.isLoading = false;
      state.error = null;
    },
    fetchSurveysFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },
    setCurrentSurvey: (state, action: PayloadAction<Survey>) => {
      state.currentSurvey = action.payload;
    },
    uploadStart: (state) => {
      state.isLoading = true;
      state.uploadProgress = 0;
      state.error = null;
    },
    uploadProgress: (state, action: PayloadAction<number>) => {
      state.uploadProgress = action.payload;
    },
    uploadSuccess: (state, action: PayloadAction<Survey>) => {
      state.surveys.unshift(action.payload);
      state.isLoading = false;
      state.uploadProgress = 100;
      state.error = null;
    },
    uploadFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.uploadProgress = 0;
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  fetchSurveysStart,
  fetchSurveysSuccess,
  fetchSurveysFailure,
  setCurrentSurvey,
  uploadStart,
  uploadProgress,
  uploadSuccess,
  uploadFailure,
  clearError,
} = surveySlice.actions;

export default surveySlice.reducer;