import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface ProcessingJob {
  id: string;
  survey: string;
  survey_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress_percentage: number;
  configuration: any;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  results_summary?: any;
  created_at: string;
  updated_at: string;
}

interface ProcessingState {
  jobs: ProcessingJob[];
  currentJob: ProcessingJob | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: ProcessingState = {
  jobs: [],
  currentJob: null,
  isLoading: false,
  error: null,
};

const processingSlice = createSlice({
  name: 'processing',
  initialState,
  reducers: {
    fetchJobsStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    fetchJobsSuccess: (state, action: PayloadAction<ProcessingJob[]>) => {
      state.jobs = action.payload;
      state.isLoading = false;
      state.error = null;
    },
    fetchJobsFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },
    createJobStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    createJobSuccess: (state, action: PayloadAction<ProcessingJob>) => {
      state.jobs.unshift(action.payload);
      state.currentJob = action.payload;
      state.isLoading = false;
      state.error = null;
    },
    createJobFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },
    updateJob: (state, action: PayloadAction<ProcessingJob>) => {
      const index = state.jobs.findIndex(job => job.id === action.payload.id);
      if (index !== -1) {
        state.jobs[index] = action.payload;
      }
      if (state.currentJob && state.currentJob.id === action.payload.id) {
        state.currentJob = action.payload;
      }
    },
    setCurrentJob: (state, action: PayloadAction<ProcessingJob>) => {
      state.currentJob = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  fetchJobsStart,
  fetchJobsSuccess,
  fetchJobsFailure,
  createJobStart,
  createJobSuccess,
  createJobFailure,
  updateJob,
  setCurrentJob,
  clearError,
} = processingSlice.actions;

export default processingSlice.reducer;