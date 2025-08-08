import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Button,
  Menu,
  MenuItem
} from '@mui/material';
import {
  MoreVert as MoreIcon,
  PlayArrow as ProcessIcon,
  Assessment as AnalyzeIcon,
  Download as DownloadIcon
} from '@mui/icons-material';

// Mock data for demonstration
const surveys = [
  {
    id: '1',
    name: 'National Sample Survey 2023',
    survey_type: 'household',
    file_type: 'csv',
    total_rows: 45000,
    total_columns: 120,
    has_weights: true,
    uploaded_by: 'survey.admin',
    created_at: '2024-01-15T10:30:00Z',
    status: 'analyzed'
  },
  {
    id: '2',
    name: 'Employment Survey Q4 2023',
    survey_type: 'employment',
    file_type: 'xlsx',
    total_rows: 28500,
    total_columns: 85,
    has_weights: true,
    uploaded_by: 'emp.analyst',
    created_at: '2024-01-14T14:20:00Z',
    status: 'uploaded'
  },
  {
    id: '3',
    name: 'Consumer Expenditure Study',
    survey_type: 'consumption',
    file_type: 'csv',
    total_rows: 67200,
    total_columns: 95,
    has_weights: false,
    uploaded_by: 'consumer.research',
    created_at: '2024-01-12T09:15:00Z',
    status: 'processing'
  }
];

const getSurveyTypeLabel = (type: string) => {
  const types: { [key: string]: string } = {
    household: 'Household Survey',
    employment: 'Employment Survey',
    consumption: 'Consumption Survey',
    enterprise: 'Enterprise Survey',
    agriculture: 'Agriculture Survey',
    other: 'Other'
  };
  return types[type] || 'Other';
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'analyzed':
      return 'success';
    case 'processing':
      return 'warning';
    case 'uploaded':
      return 'info';
    default:
      return 'default';
  }
};

export default function SurveyList() {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [selectedSurvey, setSelectedSurvey] = React.useState<string | null>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, surveyId: string) => {
    setAnchorEl(event.currentTarget);
    setSelectedSurvey(surveyId);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedSurvey(null);
  };

  const handleAction = (action: string) => {
    console.log(`Action ${action} for survey ${selectedSurvey}`);
    handleMenuClose();
  };

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
        Survey Data Files
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Manage your uploaded survey datasets
      </Typography>

      <TableContainer component={Paper} sx={{ mt: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Survey Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Format</TableCell>
              <TableCell align="right">Rows</TableCell>
              <TableCell align="right">Columns</TableCell>
              <TableCell>Weights</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Uploaded</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {surveys.map((survey) => (
              <TableRow key={survey.id} hover>
                <TableCell>
                  <Typography variant="subtitle2">
                    {survey.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    by {survey.uploaded_by}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={getSurveyTypeLabel(survey.survey_type)}
                    size="small"
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={survey.file_type.toUpperCase()}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right">
                  {survey.total_rows?.toLocaleString() || '-'}
                </TableCell>
                <TableCell align="right">
                  {survey.total_columns || '-'}
                </TableCell>
                <TableCell>
                  <Chip
                    label={survey.has_weights ? 'Yes' : 'No'}
                    size="small"
                    color={survey.has_weights ? 'success' : 'default'}
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={survey.status}
                    size="small"
                    color={getStatusColor(survey.status) as any}
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {formatDate(survey.created_at)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={(e) => handleMenuOpen(e, survey.id)}
                  >
                    <MoreIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => handleAction('analyze')}>
          <AnalyzeIcon sx={{ mr: 1 }} />
          Analyze Data
        </MenuItem>
        <MenuItem onClick={() => handleAction('process')}>
          <ProcessIcon sx={{ mr: 1 }} />
          Start Processing
        </MenuItem>
        <MenuItem onClick={() => handleAction('download')}>
          <DownloadIcon sx={{ mr: 1 }} />
          Download
        </MenuItem>
      </Menu>

      {/* Empty State */}
      {surveys.length === 0 && (
        <Paper sx={{ p: 6, textAlign: 'center', mt: 3 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No survey data uploaded yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Upload your first survey dataset to get started with data processing
          </Typography>
          <Button variant="contained" href="/upload">
            Upload Survey Data
          </Button>
        </Paper>
      )}
    </Box>
  );
}