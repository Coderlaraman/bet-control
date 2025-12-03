import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import { betsAPI } from '../services/api';

interface BetFormData {
  sport_id: number;
  league_id?: number;
  country_id?: number;
  market_id?: number;
  event_name: string;
  event_date: string;
  event_time?: string;
  home_team?: string;
  away_team?: string;
  bet_description: string;
  odds: number;
  stake: number;
  bet_slip_id?: string;
  notes?: string;
}

export const NewBet: React.FC = () => {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [smartInput, setSmartInput] = useState('');
  const [isParsing, setIsParsing] = useState(false);
  
  const { register, handleSubmit, setValue, formState: { errors } } = useForm<BetFormData>();

  const handleSmartParse = async () => {
    if (!smartInput.trim()) return;
    setIsParsing(true);
    try {
      const response = await betsAPI.parseBet(smartInput);
      const parsedData = response.data;
      
      // Auto-fill form fields
      if (parsedData.stake) setValue('stake', parsedData.stake);
      if (parsedData.home_team) setValue('home_team', parsedData.home_team);
      if (parsedData.away_team) setValue('away_team', parsedData.away_team);
      
      // Construct event name if teams are found
      if (parsedData.home_team && parsedData.away_team) {
        setValue('event_name', `${parsedData.home_team} vs ${parsedData.away_team}`);
      }
      
      // Set description
      setValue('bet_description', smartInput);
      
      // Try to map market (Basic mapping)
      if (parsedData.market) {
        // This would need a more robust mapping in a real app
        if (parsedData.market === "Match Winner") setValue('market_id', 1);
        if (parsedData.market === "Over/Under") setValue('market_id', 2);
      }

      // Set default values for required fields if missing
      setValue('sport_id', 1); // Default to Soccer
      setValue('event_date', new Date().toISOString().split('T')[0]); // Today
      
    } catch (err) {
      console.error("Error parsing bet:", err);
      setError('Could not understand the bet description. Please fill manually.');
    } finally {
      setIsParsing(false);
    }
  };

  const onSubmit = async (data: BetFormData) => {
    setError('');
    setIsLoading(true);

    try {
      // Construct ISO datetime string from date and time
      let eventDateTime = data.event_date;
      if (data.event_time) {
        eventDateTime = `${data.event_date}T${data.event_time}:00`;
      } else {
        eventDateTime = `${data.event_date}T00:00:00`;
      }

      const betData = {
        ...data,
        event_date: eventDateTime,
        event_time: undefined, // Don't send raw time string to avoid validation error
        bet_type_id: 1, // Single bet por defecto
      };
      
      await betsAPI.createBet(betData);
      navigate('/bets');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        // Handle Pydantic validation errors (list of objects)
        setError(detail.map((e: any) => e.msg).join(', '));
      } else if (typeof detail === 'object' && detail !== null) {
        // Handle generic object errors
        setError(JSON.stringify(detail));
      } else {
        // Handle string errors or default
        // If detail is not provided (e.g. 500 error), try to use statusText or fallback
        setError(detail || err.response?.statusText || 'Error creating bet');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Place New Bet
      </Typography>

      <Paper sx={{ p: 3 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Smart Entry Section */}
        <Box sx={{ mb: 4, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
          <Typography variant="h6" gutterBottom>
            Smart Bet Entry (AI Powered)
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Describe your bet naturally (e.g., "I bet 50 dollars on Real Madrid to beat Barcelona") or use voice input.
          </Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={10}>
              <TextField
                fullWidth
                placeholder="Type your bet here..."
                value={smartInput}
                onChange={(e) => setSmartInput(e.target.value)}
                disabled={isParsing}
              />
            </Grid>
            <Grid item xs={12} md={2}>
               <Button 
                fullWidth 
                variant="contained" 
                color="secondary"
                onClick={handleSmartParse}
                disabled={isParsing || !smartInput}
              >
                {isParsing ? 'Analyzing...' : 'Auto-Fill'}
              </Button>
            </Grid>
            <Grid item xs={12}>
               {/* Placeholder for Voice Input - Roadmap Feature */}
               <Button variant="text" startIcon={<span role="img" aria-label="mic">🎤</span>} disabled>
                 Voice Input (Coming Soon)
               </Button>
            </Grid>
          </Grid>
        </Box>

        <form onSubmit={handleSubmit(onSubmit)}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Event Name"
                {...register('event_name', { required: 'Event name is required' })}
                error={!!errors.event_name}
                helperText={errors.event_name?.message}
              />
            </Grid>

            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Event Date"
                type="date"
                InputLabelProps={{ shrink: true }}
                {...register('event_date', { required: 'Event date is required' })}
                error={!!errors.event_date}
                helperText={errors.event_date?.message}
              />
            </Grid>

            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Event Time"
                type="time"
                InputLabelProps={{ shrink: true }}
                {...register('event_time')}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Home Team"
                {...register('home_team')}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Away Team"
                {...register('away_team')}
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Sport</InputLabel>
                <Select
                  label="Sport"
                  {...register('sport_id', { required: 'Sport is required' })}
                  defaultValue=""
                >
                  <MenuItem value={1}>Soccer</MenuItem>
                  <MenuItem value={2}>Basketball</MenuItem>
                  <MenuItem value={3}>Tennis</MenuItem>
                  <MenuItem value={4}>Baseball</MenuItem>
                  <MenuItem value={5}>American Football</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Market</InputLabel>
                <Select
                  label="Market"
                  {...register('market_id')}
                  defaultValue=""
                >
                  <MenuItem value={1}>Match Winner</MenuItem>
                  <MenuItem value={2}>Over/Under</MenuItem>
                  <MenuItem value={3}>Handicap</MenuItem>
                  <MenuItem value={4}>Both Teams to Score</MenuItem>
                  <MenuItem value={5}>Correct Score</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="League"
                {...register('league_id')}
                type="number"
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Bet Description"
                multiline
                rows={2}
                {...register('bet_description', { required: 'Bet description is required' })}
                error={!!errors.bet_description}
                helperText={errors.bet_description?.message}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Odds"
                type="number"
                inputProps={{ step: '0.01' }}
                {...register('odds', { 
                  required: 'Odds are required',
                  min: { value: 1.01, message: 'Odds must be greater than 1.01' }
                })}
                error={!!errors.odds}
                helperText={errors.odds?.message}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Stake"
                type="number"
                inputProps={{ step: '0.01' }}
                {...register('stake', { 
                  required: 'Stake is required',
                  min: { value: 0.01, message: 'Stake must be greater than 0.01' }
                })}
                error={!!errors.stake}
                helperText={errors.stake?.message}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Bet Slip ID"
                {...register('bet_slip_id')}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Notes"
                multiline
                rows={2}
                {...register('notes')}
              />
            </Grid>

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={isLoading}
                >
                  {isLoading ? 'Creating Bet...' : 'Create Bet'}
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/bets')}
                >
                  Cancel
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  );
};