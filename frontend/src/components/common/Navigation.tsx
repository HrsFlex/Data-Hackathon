import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Paper,
  Typography,
  Box
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  CloudUpload as UploadIcon,
  List as ListIcon,
  Settings as ProcessingIcon
} from '@mui/icons-material';

const navigationItems = [
  { path: '/', label: 'Dashboard', icon: <DashboardIcon /> },
  { path: '/upload', label: 'Upload Survey', icon: <UploadIcon /> },
  { path: '/surveys', label: 'Survey List', icon: <ListIcon /> },
  { path: '/processing', label: 'Processing Jobs', icon: <ProcessingIcon /> },
];

export default function Navigation() {
  const location = useLocation();

  return (
    <Paper elevation={1} sx={{ width: 240, height: 'fit-content', p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2, color: 'text.secondary' }}>
        Navigation
      </Typography>
      <List>
        {navigationItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
              sx={{ borderRadius: 1 }}
            >
              <ListItemIcon>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      
      <Box sx={{ mt: 4, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
        <Typography variant="caption" color="text.secondary">
          Government of India
          <br />
          Ministry of Statistics and
          <br />
          Programme Implementation
        </Typography>
      </Box>
    </Paper>
  );
}