import React from 'react';
import { useQuery } from 'react-query';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { betsAPI, bankrollAPI } from '../services/api';

const COLORS = ['#4caf50', '#f44336', '#ff9800', '#2196f3'];

export const Dashboard: React.FC = () => {
  const { data: bettingStats, isLoading: statsLoading, error: statsError } = useQuery(
    'bettingStats',
    () => betsAPI.getBettingStats().then(res => res.data)
  );

  const { data: bankrollSummary, isLoading: bankrollLoading, error: bankrollError } = useQuery(
    'bankrollSummary',
    () => bankrollAPI.getSummary().then(res => res.data)
  );

  if (statsLoading || bankrollLoading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
      </Box>
    );
  }

  if (statsError || bankrollError) {
    return (
      <Alert severity="error">
        Error loading dashboard data. Please try again later.
      </Alert>
    );
  }

  const pieData = bettingStats ? [
    { name: 'Won', value: bettingStats.won_bets },
    { name: 'Lost', value: bettingStats.lost_bets },
    { name: 'Void', value: bettingStats.void_bets },
    { name: 'Pending', value: bettingStats.pending_bets },
  ] : [];

  const barData = bettingStats ? [
    {
      name: 'Total Staked',
      value: bettingStats.total_staked,
    },
    {
      name: 'Total Won',
      value: bettingStats.total_won,
    },
    {
      name: 'Profit/Loss',
      value: bettingStats.total_profit,
    },
  ] : [];

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* Bankroll Summary */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Current Bankroll
              </Typography>
              <Typography variant="h4" component="h2">
                ${bankrollSummary?.current_amount.toFixed(2)}
              </Typography>
              <Typography color="textSecondary">
                Initial: ${bankrollSummary?.initial_amount.toFixed(2)}
              </Typography>
              <Typography 
                variant="h6" 
                color={bankrollSummary && bankrollSummary.profit_loss >= 0 ? 'success.main' : 'error.main'}
              >
                {bankrollSummary && bankrollSummary.profit_loss >= 0 ? '+' : ''}
                ${bankrollSummary?.profit_loss.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Win Rate */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Win Rate
              </Typography>
              <Typography variant="h4" component="h2">
                {bettingStats?.win_rate.toFixed(1)}%
              </Typography>
              <Typography color="textSecondary">
                {bettingStats?.won_bets} won / {bettingStats?.total_bets} total
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* ROI */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                ROI
              </Typography>
              <Typography 
                variant="h4" 
                component="h2"
                color={bettingStats && bettingStats.roi >= 0 ? 'success.main' : 'error.main'}
              >
                {bettingStats && bettingStats.roi >= 0 ? '+' : ''}
                {bettingStats?.roi.toFixed(2)}%
              </Typography>
              <Typography color="textSecondary">
                Return on Investment
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Bets Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Bets Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Financial Overview */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Financial Overview
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={barData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value) => `$${Number(value).toFixed(2)}`} />
                  <Legend />
                  <Bar dataKey="value">
                    {barData.map((entry, index) => (
                      <Cell key={'bar-cell-' + index} fill={entry.value >= 0 ? '#4caf50' : '#f44336'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Transactions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Bankroll Transactions
              </Typography>
              {bankrollSummary?.recent_transactions?.slice(0, 5).map((transaction, index) => (
                <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                  <Typography variant="body2">
                    {transaction.type.replace('_', ' ').toUpperCase()}
                  </Typography>
                  <Typography 
                    variant="body2"
                    color={transaction.amount >= 0 ? 'success.main' : 'error.main'}
                  >
                    {transaction.amount >= 0 ? '+' : ''}
                    ${transaction.amount.toFixed(2)}
                  </Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};