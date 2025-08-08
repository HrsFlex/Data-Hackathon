import React from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  LinearProgress,
  Chip
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Assessment as ProcessingIcon,
  Description as ReportIcon,
  CheckCircle as CompletedIcon
} from '@mui/icons-material';

// Mock data for demonstration
const dashboardStats = {
  totalSurveys: 15,
  activeJobs: 3,
  completedJobs: 12,
  generatedReports: 8
};

const recentActivity = [
  { id: 1, type: 'upload', title: 'Household Survey 2023 uploaded', time: '2 hours ago', status: 'completed' },
  { id: 2, type: 'processing', title: 'Employment Survey processing started', time: '4 hours ago', status: 'in_progress' },
  { id: 3, type: 'report', title: 'Consumer Expenditure report generated', time: '1 day ago', status: 'completed' },
  { id: 4, type: 'processing', title: 'Agriculture Survey analysis completed', time: '2 days ago', status: 'completed' },
];

export default function Dashboard() {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Overview of your survey data processing activities
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <UploadIcon color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Total Surveys
                  </Typography>
                  <Typography variant="h5">
                    {dashboardStats.totalSurveys}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <ProcessingIcon color="warning" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Active Jobs
                  </Typography>
                  <Typography variant="h5">
                    {dashboardStats.activeJobs}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CompletedIcon color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Completed Jobs
                  </Typography>
                  <Typography variant="h5">
                    {dashboardStats.completedJobs}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <ReportIcon color="info" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Generated Reports
                  </Typography>
                  <Typography variant="h5">
                    {dashboardStats.generatedReports}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <Box>
              {recentActivity.map((activity) => (
                <Box
                  key={activity.id}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    py: 2,
                    borderBottom: '1px solid',
                    borderColor: 'divider',
                    '&:last-child': { borderBottom: 'none' }
                  }}
                >
                  <Box>
                    <Typography variant="body1">
                      {activity.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {activity.time}
                    </Typography>
                  </Box>
                  <Chip
                    label={activity.status === 'completed' ? 'Completed' : 'In Progress'}
                    color={activity.status === 'completed' ? 'success' : 'warning'}
                    size="small"
                  />
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              System Status
            </Typography>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Processing Capacity
              </Typography>
              <LinearProgress variant="determinate" value={65} sx={{ mt: 1 }} />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                65% utilized
              </Typography>
            </Box>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Storage Used
              </Typography>
              <LinearProgress variant="determinate" value={42} sx={{ mt: 1 }} />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                2.1 GB of 5 GB used
              </Typography>
            </Box>
          </Paper>
          
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Typography variant="body2" color="text.secondary">
              • Upload a new survey dataset
              <br />
              • Configure data cleaning rules
              <br />
              • Generate statistical reports
              <br />
              • Export processed data
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}