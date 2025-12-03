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
  
  const { register, handleSubmit, formState: { errors }, reset } = useForm<BetFormData>();

  const onSubmit = async (data: BetFormData) => {
    setError('');
    setIsLoading(true);

    try {
      const betData = {
        ...data,
        bet_type_id: 1, // Single bet por defecto
      };
      
      await betsAPI.createBet(betData);
      navigate('/bets');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error creating bet');
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