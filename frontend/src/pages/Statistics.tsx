import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { betsAPI } from '../services/api';

const COLORS = ['#4caf50', '#f44336', '#ff9800', '#2196f3'];

export const Statistics: React.FC = () => {
  const [timeRange, setTimeRange] = useState('30');
  const [sportFilter, setSportFilter] = useState('all');

  const { data: bettingStats } = useQuery(
    'bettingStats',
    () => betsAPI.getBettingStats().then(res => res.data)
  );

  // Mock data para gráficos (en producción vendría del backend)
  const mockMonthlyData = [
    { month: 'Jan', bets: 25, profit: 125, winRate: 52 },
    { month: 'Feb', bets: 30, profit: -50, winRate: 48 },
    { month: 'Mar', bets: 28, profit: 200, winRate: 55 },
    { month: 'Apr', bets: 32, profit: 75, winRate: 51 },
    { month: 'May', bets: 35, profit: -25, winRate: 49 },
    { month: 'Jun', bets: 29, profit: 150, winRate: 53 },
  ];

  const mockSportData = [
    { sport: 'Soccer', bets: 45, profit: 250, winRate: 54 },
    { sport: 'Basketball', bets: 25, profit: -75, winRate: 47 },
    { sport: 'Tennis', bets: 30, profit: 100, winRate: 52 },
    { sport: 'Baseball', bets: 20, profit: 50, winRate: 51 },
  ];

  const pieData = bettingStats ? [
    { name: 'Won', value: bettingStats.won_bets },
    { name: 'Lost', value: bettingStats.lost_bets },
    { name: 'Void', value: bettingStats.void_bets },
    { name: 'Pending', value: bettingStats.pending_bets },
  ] : [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Betting Statistics
      </Typography>

      {/* Filters */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Time Range</InputLabel>
              <Select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                label="Time Range"
              >
                <MenuItem value="7">Last 7 days</MenuItem>
                <MenuItem value="30">Last 30 days</MenuItem>
                <MenuItem value="90">Last 90 days</MenuItem>
                <MenuItem value="365">Last year</MenuItem>
                <MenuItem value="all">All time</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Sport</InputLabel>
              <Select
                value={sportFilter}
                onChange={(e) => setSportFilter(e.target.value)}
                label="Sport"
              >
                <MenuItem value="all">All Sports</MenuItem>
                <MenuItem value="soccer">Soccer</MenuItem>
                <MenuItem value="basketball">Basketball</MenuItem>
                <MenuItem value="tennis">Tennis</MenuItem>
                <MenuItem value="baseball">Baseball</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Box>

      {/* Key Statistics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Bets
              </Typography>
              <Typography variant="h4">
                {bettingStats?.total_bets || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Win Rate
              </Typography>
              <Typography variant="h4">
                {bettingStats?.win_rate.toFixed(1) || 0}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Profit
              </Typography>
              {(() => {
                const totalProfit = bettingStats?.total_profit ?? 0;
                return (
                  <Typography variant="h4" color={totalProfit >= 0 ? 'success.main' : 'error.main'}>
                    {totalProfit >= 0 ? '+' : ''}
                    ${totalProfit.toFixed(2)}
                  </Typography>
                );
              })()}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                ROI
              </Typography>
              {(() => {
                const roi = bettingStats?.roi ?? 0;
                return (
                  <Typography variant="h4" color={roi >= 0 ? 'success.main' : 'error.main'}>
                    {roi.toFixed(2)}%
                  </Typography>
                );
              })()}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {/* Monthly Performance */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Monthly Performance
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={mockMonthlyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="profit" stroke="#4caf50" fill="#4caf50" fillOpacity={0.3} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Bets Distribution */}
        <Grid item xs={12} md={4}>
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

        {/* Sport Performance */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance by Sport
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={mockSportData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="sport" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="bets" fill="#2196f3" name="Bets" />
                  <Bar dataKey="profit" fill="#4caf50" name="Profit" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Win Rate by Sport */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Win Rate by Sport
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={mockSportData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="sport" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="winRate" stroke="#ff9800" name="Win Rate (%)" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Detailed Stats Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Detailed Statistics
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Metric</TableCell>
                      <TableCell align="right">Value</TableCell>
                      <TableCell align="right">Change</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell>Total Bets</TableCell>
                      <TableCell align="right">{bettingStats?.total_bets || 0}</TableCell>
                      <TableCell align="right">+12%</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Won Bets</TableCell>
                      <TableCell align="right">{bettingStats?.won_bets || 0}</TableCell>
                      <TableCell align="right">+8%</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Lost Bets</TableCell>
                      <TableCell align="right">{bettingStats?.lost_bets || 0}</TableCell>
                      <TableCell align="right">+4%</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Void Bets</TableCell>
                      <TableCell align="right">{bettingStats?.void_bets || 0}</TableCell>
                      <TableCell align="right">0%</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Total Staked</TableCell>
                      <TableCell align="right">${bettingStats?.total_staked.toFixed(2) || 0}</TableCell>
                      <TableCell align="right">+15%</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Total Won</TableCell>
                      <TableCell align="right">${bettingStats?.total_won.toFixed(2) || 0}</TableCell>
                      <TableCell align="right">+18%</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>ROI</TableCell>
                      <TableCell align="right">{bettingStats?.roi.toFixed(2) || 0}%</TableCell>
                      <TableCell align="right">+2.5%</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};