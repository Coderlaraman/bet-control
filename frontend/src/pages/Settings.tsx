import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Divider,
  Switch,
  FormControlLabel,
} from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';

export const Settings: React.FC = () => {
  const [settings, setSettings] = useState({
    maxBetPercentage: 5.0,
    minBetAmount: 10.0,
    maxBetAmount: 500.0,
    currency: 'USD',
    notifications: true,
    emailAlerts: true,
    autoSettlement: false,
    riskLevel: 'medium',
  });

  const [success, setSuccess] = useState(false);
  const [error] = useState('');

  const handleChange = (field: string, value: any) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    // En producción, enviar al backend
    setSuccess(true);
    setTimeout(() => setSuccess(false), 3000);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Settings saved successfully!
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Betting Limits */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Betting Limits
              </Typography>
              
              <TextField
                fullWidth
                label="Max Bet Percentage (%)"
                type="number"
                value={settings.maxBetPercentage}
                onChange={(e) => handleChange('maxBetPercentage', parseFloat(e.target.value))}
                inputProps={{ step: 0.1, min: 0.1, max: 100 }}
                helperText="Maximum percentage of bankroll per bet"
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                label="Minimum Bet Amount"
                type="number"
                value={settings.minBetAmount}
                onChange={(e) => handleChange('minBetAmount', parseFloat(e.target.value))}
                inputProps={{ step: 0.01, min: 0.01 }}
                helperText="Minimum allowed bet amount"
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                label="Maximum Bet Amount"
                type="number"
                value={settings.maxBetAmount}
                onChange={(e) => handleChange('maxBetAmount', parseFloat(e.target.value))}
                inputProps={{ step: 0.01, min: 0.01 }}
                helperText="Maximum allowed bet amount"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Preferences */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Preferences
              </Typography>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Currency</InputLabel>
                <Select
                  value={settings.currency}
                  onChange={(e) => handleChange('currency', e.target.value)}
                  label="Currency"
                >
                  <MenuItem value="USD">USD - US Dollar</MenuItem>
                  <MenuItem value="EUR">EUR - Euro</MenuItem>
                  <MenuItem value="GBP">GBP - British Pound</MenuItem>
                  <MenuItem value="COP">COP - Colombian Peso</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth>
                <InputLabel>Risk Level</InputLabel>
                <Select
                  value={settings.riskLevel}
                  onChange={(e) => handleChange('riskLevel', e.target.value)}
                  label="Risk Level"
                >
                  <MenuItem value="low">Low Risk</MenuItem>
                  <MenuItem value="medium">Medium Risk</MenuItem>
                  <MenuItem value="high">High Risk</MenuItem>
                </Select>
              </FormControl>
            </CardContent>
          </Card>
        </Grid>

        {/* Notifications */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Notifications
              </Typography>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications}
                    onChange={(e) => handleChange('notifications', e.target.checked)}
                  />
                }
                label="Enable notifications"
                sx={{ mb: 2, display: 'block' }}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.emailAlerts}
                    onChange={(e) => handleChange('emailAlerts', e.target.checked)}
                  />
                }
                label="Email alerts for bet settlements"
                sx={{ mb: 2, display: 'block' }}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoSettlement}
                    onChange={(e) => handleChange('autoSettlement', e.target.checked)}
                  />
                }
                label="Auto-settle pending bets after 72 hours"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Save Button */}
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              size="large"
            >
              Save Settings
            </Button>
          </Box>
        </Grid>
      </Grid>

      {/* Additional Settings */}
      <Divider sx={{ my: 4 }} />

      <Typography variant="h5" gutterBottom>
        Advanced Settings
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Data Export
              </Typography>
              
              <Button
                variant="outlined"
                sx={{ mr: 2, mb: 1 }}
              >
                Export to CSV
              </Button>
              
              <Button
                variant="outlined"
                sx={{ mb: 1 }}
              >
                Export to Excel
              </Button>
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Download your betting history and statistics
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Account Management
              </Typography>
              
              <Button
                variant="outlined"
                color="warning"
                sx={{ mr: 2, mb: 1 }}
              >
                Reset Statistics
              </Button>
              
              <Button
                variant="outlined"
                color="error"
                sx={{ mb: 1 }}
              >
                Delete Account
              </Button>
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Use with caution - these actions cannot be undone
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};