import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Container, AppBar, Toolbar, Typography, Box } from '@mui/material';
import Dashboard from './pages/Dashboard';
import SurveyUpload from './pages/SurveyUpload';
import SurveyList from './pages/SurveyList';
import ProcessingJobs from './pages/ProcessingJobs';
import Navigation from './components/common/Navigation';

function App() {
  return (
    <div className="App">
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            AI-Enhanced Survey Data Processing
          </Typography>
          <Typography variant="subtitle2" component="div">
            MoSPI Initiative
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex' }}>
          <Navigation />
          <Box component="main" sx={{ flexGrow: 1, ml: 3 }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/upload" element={<SurveyUpload />} />
              <Route path="/surveys" element={<SurveyList />} />
              <Route path="/processing" element={<ProcessingJobs />} />
            </Routes>
          </Box>
        </Box>
      </Container>
    </div>
  );
}

export default App;