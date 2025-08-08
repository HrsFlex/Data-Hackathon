import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Report {
  id: string;
  title: string;
  format: 'pdf' | 'html';
  status: 'pending' | 'generating' | 'completed' | 'failed';
  file_size?: number;
  created_at: string;
  generation_time?: number;
  survey_name: string;
  job_id: string;
  download_url?: string;
}

interface ReportState {
  reports: Report[];
  isLoading: boolean;
  isGenerating: boolean;
  error: string | null;
}

const initialState: ReportState = {
  reports: [],
  isLoading: false,
  isGenerating: false,
  error: null,
};

const reportSlice = createSlice({
  name: 'reports',
  initialState,
  reducers: {
    fetchReportsStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    fetchReportsSuccess: (state, action: PayloadAction<Report[]>) => {
      state.reports = action.payload;
      state.isLoading = false;
      state.error = null;
    },
    fetchReportsFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },
    generateReportStart: (state) => {
      state.isGenerating = true;
      state.error = null;
    },
    generateReportSuccess: (state, action: PayloadAction<Report>) => {
      state.reports.unshift(action.payload);
      state.isGenerating = false;
      state.error = null;
    },
    generateReportFailure: (state, action: PayloadAction<string>) => {
      state.isGenerating = false;
      state.error = action.payload;
    },
    updateReport: (state, action: PayloadAction<Report>) => {
      const index = state.reports.findIndex(report => report.id === action.payload.id);
      if (index !== -1) {
        state.reports[index] = action.payload;
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  fetchReportsStart,
  fetchReportsSuccess,
  fetchReportsFailure,
  generateReportStart,
  generateReportSuccess,
  generateReportFailure,
  updateReport,
  clearError,
} = reportSlice.actions;

export default reportSlice.reducer;