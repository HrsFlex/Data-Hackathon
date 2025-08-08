import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Alert,
  LinearProgress,
  Chip
} from '@mui/material';
import { CloudUpload as UploadIcon } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

const surveyTypes = [
  { value: 'household', label: 'Household Survey' },
  { value: 'enterprise', label: 'Enterprise Survey' },
  { value: 'agriculture', label: 'Agriculture Survey' },
  { value: 'consumption', label: 'Consumption Expenditure Survey' },
  { value: 'employment', label: 'Employment Survey' },
  { value: 'other', label: 'Other' },
];

export default function SurveyUpload() {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    survey_type: 'other',
    has_weights: false,
    weight_column: ''
  });
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setUploadFile(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    multiple: false,
    maxSize: 100 * 1024 * 1024 // 100MB
  });

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    setUploadProgress(0);

    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(interval);
          return prev;
        }
        return prev + 10;
      });
    }, 200);

    try {
      // In real implementation, this would call the API
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setUploadProgress(100);
      setUploadStatus('success');
      
      // Reset form after successful upload
      setTimeout(() => {
        setFormData({
          name: '',
          description: '',
          survey_type: 'other',
          has_weights: false,
          weight_column: ''
        });
        setUploadFile(null);
        setUploadStatus('idle');
        setUploadProgress(0);
      }, 3000);
    } catch (error) {
      setUploadStatus('error');
    } finally {
      setUploading(false);
      clearInterval(interval);
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Upload Survey Data
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Upload CSV or Excel files containing survey data for processing
      </Typography>

      <Paper sx={{ p: 4, mt: 3 }}>
        <form onSubmit={handleSubmit}>
          {/* File Upload Area */}
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.400',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: isDragActive ? 'primary.light' : 'grey.50',
              mb: 3,
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: 'primary.light'
              }
            }}
          >
            <input {...getInputProps()} />
            <UploadIcon sx={{ fontSize: 48, color: 'grey.500', mb: 2 }} />
            {uploadFile ? (
              <Box>
                <Typography variant="h6" color="success.main">
                  File Selected: {uploadFile.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Size: {(uploadFile.size / 1024 / 1024).toFixed(2)} MB
                </Typography>
                <Chip
                  label={uploadFile.type}
                  size="small"
                  sx={{ mt: 1 }}
                />
              </Box>
            ) : (
              <Box>
                <Typography variant="h6" gutterBottom>
                  {isDragActive
                    ? "Drop the file here..."
                    : "Drag & drop a survey file here, or click to select"}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Supported formats: CSV, XLS, XLSX (Max size: 100MB)
                </Typography>
              </Box>
            )}
          </Box>

          {/* Survey Information */}
          <Box sx={{ mb: 3 }}>
            <TextField
              fullWidth
              label="Survey Name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              required
              sx={{ mb: 2 }}
            />
            
            <TextField
              fullWidth
              label="Description"
              multiline
              rows={3}
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              sx={{ mb: 2 }}
            />
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Survey Type</InputLabel>
              <Select
                value={formData.survey_type}
                onChange={(e) => handleInputChange('survey_type', e.target.value)}
                label="Survey Type"
              >
                {surveyTypes.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.has_weights}
                  onChange={(e) => handleInputChange('has_weights', e.target.checked)}
                />
              }
              label="This survey has design weights"
              sx={{ mb: 2 }}
            />

            {formData.has_weights && (
              <TextField
                fullWidth
                label="Weight Column Name"
                value={formData.weight_column}
                onChange={(e) => handleInputChange('weight_column', e.target.value)}
                helperText="Enter the exact column name that contains the survey weights"
              />
            )}
          </Box>

          {/* Upload Progress */}
          {uploading && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" gutterBottom>
                Uploading... {uploadProgress}%
              </Typography>
              <LinearProgress variant="determinate" value={uploadProgress} />
            </Box>
          )}

          {/* Status Messages */}
          {uploadStatus === 'success' && (
            <Alert severity="success" sx={{ mb: 3 }}>
              Survey uploaded successfully! You can now proceed to configure data processing.
            </Alert>
          )}

          {uploadStatus === 'error' && (
            <Alert severity="error" sx={{ mb: 3 }}>
              Upload failed. Please try again or contact support.
            </Alert>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            variant="contained"
            size="large"
            disabled={!uploadFile || !formData.name || uploading}
            sx={{ mt: 2 }}
          >
            {uploading ? 'Uploading...' : 'Upload Survey'}
          </Button>
        </form>
      </Paper>

      {/* Guidelines */}
      <Paper sx={{ p: 3, mt: 3, bgcolor: 'info.light', color: 'info.contrastText' }}>
        <Typography variant="h6" gutterBottom>
          Upload Guidelines
        </Typography>
        <Typography variant="body2" component="div">
          • Ensure your data file is in CSV, XLS, or XLSX format
          <br />
          • First row should contain column headers
          <br />
          • Avoid special characters in column names
          <br />
          • Missing values can be left blank or marked as NA
          <br />
          • If using weights, specify the exact column name
          <br />
          • Maximum file size is 100MB
        </Typography>
      </Paper>
    </Box>
  );
}