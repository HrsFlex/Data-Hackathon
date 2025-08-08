import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Button,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Stepper,
  Step,
  StepLabel
} from '@mui/material';
import {
  CheckCircle as CompletedIcon,
  RadioButtonUnchecked as PendingIcon,
  Cancel as CancelledIcon,
  PlayArrow as RunningIcon
} from '@mui/icons-material';

// Mock data for demonstration
const processingJobs = [
  {
    id: '1',
    survey_name: 'National Sample Survey 2023',
    status: 'running',
    progress_percentage: 65,
    created_at: '2024-01-15T14:30:00Z',
    current_step: 'Statistical Estimation',
    steps: [
      { name: 'Data Validation', status: 'completed' },
      { name: 'Data Cleaning', status: 'completed' },
      { name: 'Missing Value Imputation', status: 'completed' },
      { name: 'Outlier Detection', status: 'completed' },
      { name: 'Rule-based Validation', status: 'completed' },
      { name: 'Weight Application', status: 'running' },
      { name: 'Statistical Estimation', status: 'pending' },
      { name: 'Report Generation', status: 'pending' }
    ]
  },
  {
    id: '2',
    survey_name: 'Employment Survey Q4 2023',
    status: 'completed',
    progress_percentage: 100,
    created_at: '2024-01-14T09:15:00Z',
    current_step: 'Completed',
    steps: [
      { name: 'Data Validation', status: 'completed' },
      { name: 'Data Cleaning', status: 'completed' },
      { name: 'Missing Value Imputation', status: 'completed' },
      { name: 'Outlier Detection', status: 'completed' },
      { name: 'Rule-based Validation', status: 'completed' },
      { name: 'Weight Application', status: 'completed' },
      { name: 'Statistical Estimation', status: 'completed' },
      { name: 'Report Generation', status: 'completed' }
    ]
  },
  {
    id: '3',
    survey_name: 'Consumer Expenditure Study',
    status: 'failed',
    progress_percentage: 25,
    created_at: '2024-01-12T16:45:00Z',
    current_step: 'Failed at Data Cleaning',
    error_message: 'Invalid data format in column "income_bracket"'
  }
];

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'running':
      return 'warning';
    case 'failed':
      return 'error';
    case 'cancelled':
      return 'default';
    default:
      return 'info';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CompletedIcon color="success" />;
    case 'running':
      return <RunningIcon color="warning" />;
    case 'failed':
      return <CancelledIcon color="error" />;
    default:
      return <PendingIcon color="disabled" />;
  }
};

const getStepIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CompletedIcon color="success" fontSize="small" />;
    case 'running':
      return <RunningIcon color="warning" fontSize="small" />;
    case 'failed':
      return <CancelledIcon color="error" fontSize="small" />;
    default:
      return <PendingIcon color="disabled" fontSize="small" />;
  }
};

export default function ProcessingJobs() {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Processing Jobs
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Monitor the progress of your data processing jobs
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        {processingJobs.map((job) => (
          <Grid item xs={12} key={job.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  {getStatusIcon(job.status)}
                  <Box sx={{ ml: 2, flexGrow: 1 }}>
                    <Typography variant="h6">
                      {job.survey_name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Started: {formatDate(job.created_at)}
                    </Typography>
                  </Box>
                  <Chip
                    label={job.status.toUpperCase()}
                    color={getStatusColor(job.status) as any}
                  />
                </Box>

                {/* Progress Bar */}
                <Box sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">
                      Current Step: {job.current_step}
                    </Typography>
                    <Typography variant="body2">
                      {job.progress_percentage}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={job.progress_percentage}
                    color={job.status === 'failed' ? 'error' : 'primary'}
                  />
                </Box>

                {/* Error Message */}
                {job.status === 'failed' && (
                  <Paper sx={{ p: 2, bgcolor: 'error.light', color: 'error.contrastText', mb: 3 }}>
                    <Typography variant="body2">
                      <strong>Error:</strong> {job.error_message}
                    </Typography>
                  </Paper>
                )}

                {/* Processing Steps */}
                {job.steps && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Processing Steps
                    </Typography>
                    <List dense>
                      {job.steps.map((step, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            {getStepIcon(step.status)}
                          </ListItemIcon>
                          <ListItemText
                            primary={step.name}
                            secondary={step.status === 'running' ? 'In Progress...' : step.status}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}

                {/* Action Buttons */}
                <Box sx={{ mt: 3, display: 'flex', gap: 1 }}>
                  {job.status === 'running' && (
                    <Button variant="outlined" color="warning" size="small">
                      Pause Job
                    </Button>
                  )}
                  {job.status === 'completed' && (
                    <>
                      <Button variant="contained" size="small">
                        Download Report
                      </Button>
                      <Button variant="outlined" size="small">
                        View Results
                      </Button>
                    </>
                  )}
                  {job.status === 'failed' && (
                    <Button variant="outlined" color="primary" size="small">
                      Retry Job
                    </Button>
                  )}
                  <Button variant="text" size="small" color="error">
                    Delete
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Empty State */}
      {processingJobs.length === 0 && (
        <Paper sx={{ p: 6, textAlign: 'center', mt: 3 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No processing jobs yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Start processing your survey data to see jobs here
          </Typography>
          <Button variant="contained" href="/surveys">
            Process Survey Data
          </Button>
        </Paper>
      )}
    </Box>
  );
}