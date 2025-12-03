import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AccountBalance as AccountBalanceIcon,
} from '@mui/icons-material';
import { bankrollAPI } from '../services/api';

export const Bankroll: React.FC = () => {
  const queryClient = useQueryClient();
  const [openDeposit, setOpenDeposit] = useState(false);
  const [openWithdraw, setOpenWithdraw] = useState(false);
  const [amount, setAmount] = useState('');
  const [error, setError] = useState('');

  const { data: summary, isLoading, error: loadError } = useQuery(
    'bankrollSummary',
    () => bankrollAPI.getSummary().then(res => res.data)
  );

  const depositMutation = useMutation(
    (amount: number) => bankrollAPI.deposit({ amount }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('bankrollSummary');
        setOpenDeposit(false);
        setAmount('');
        setError('');
      },
      onError: (error: any) => {
        setError(error.response?.data?.detail || 'Error processing deposit');
      },
    }
  );

  const withdrawMutation = useMutation(
    (amount: number) => bankrollAPI.withdraw({ amount }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('bankrollSummary');
        setOpenWithdraw(false);
        setAmount('');
        setError('');
      },
      onError: (error: any) => {
        setError(error.response?.data?.detail || 'Error processing withdrawal');
      },
    }
  );

  const handleDeposit = () => {
    const numAmount = parseFloat(amount);
    if (numAmount <= 0) {
      setError('Amount must be greater than 0');
      return;
    }
    depositMutation.mutate(numAmount);
  };

  const handleWithdraw = () => {
    const numAmount = parseFloat(amount);
    if (numAmount <= 0) {
      setError('Amount must be greater than 0');
      return;
    }
    withdrawMutation.mutate(numAmount);
  };

  if (isLoading) return <LinearProgress />;
  if (loadError) return <Alert severity="error">Error loading bankroll data</Alert>;

  const profitLoss = summary?.profit_loss ?? 0;
  const profitLossColor = profitLoss >= 0 ? 'success.main' : 'error.main';
  const profitLossIcon = profitLoss >= 0 ? <TrendingUpIcon /> : <TrendingDownIcon />;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Bankroll Management
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AccountBalanceIcon color="primary" sx={{ mr: 1 }} />
                <Typography color="textSecondary" gutterBottom>
                  Current Balance
                </Typography>
              </Box>
              <Typography variant="h4">
                ${summary?.current_amount.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                {profitLossIcon}
                <Typography color="textSecondary" gutterBottom sx={{ ml: 1 }}>
                  Profit/Loss
                </Typography>
              </Box>
              <Typography variant="h4" color={profitLossColor}>
                {profitLoss >= 0 ? '+' : ''}
                ${profitLoss.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Initial Amount
              </Typography>
              <Typography variant="h4">
                ${summary?.initial_amount.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Max Bet Allowed
              </Typography>
              <Typography variant="h4">
                ${summary?.max_bet_allowed.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Action Buttons */}
      <Box sx={{ mb: 4 }}>
        <Button
          variant="contained"
          color="success"
          onClick={() => setOpenDeposit(true)}
          sx={{ mr: 2 }}
        >
          Deposit Funds
        </Button>
        <Button
          variant="contained"
          color="warning"
          onClick={() => setOpenWithdraw(true)}
        >
          Withdraw Funds
        </Button>
      </Box>

      {/* Recent Transactions */}
      <Typography variant="h6" gutterBottom>
        Recent Transactions
      </Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Amount</TableCell>
              <TableCell>Balance Before</TableCell>
              <TableCell>Balance After</TableCell>
              <TableCell>Description</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {summary?.recent_transactions?.map((transaction: any, index: number) => (
              <TableRow key={index}>
                <TableCell>
                  {new Date(transaction.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell>{transaction.type}</TableCell>
                <TableCell>
                  <Typography color={transaction.amount >= 0 ? 'success.main' : 'error.main'}>
                    {transaction.amount >= 0 ? '+' : ''}
                    ${transaction.amount.toFixed(2)}
                  </Typography>
                </TableCell>
                <TableCell>${transaction.balance_before.toFixed(2)}</TableCell>
                <TableCell>${transaction.balance_after.toFixed(2)}</TableCell>
                <TableCell>{transaction.description}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Deposit Dialog */}
      <Dialog open={openDeposit} onClose={() => setOpenDeposit(false)}>
        <DialogTitle>Deposit Funds</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <TextField
            autoFocus
            margin="dense"
            label="Amount"
            type="number"
            fullWidth
            variant="outlined"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            inputProps={{ step: "0.01", min: "0.01" }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDeposit(false)}>Cancel</Button>
          <Button 
            onClick={handleDeposit} 
            variant="contained"
            disabled={depositMutation.isLoading}
          >
            Deposit
          </Button>
        </DialogActions>
      </Dialog>

      {/* Withdraw Dialog */}
      <Dialog open={openWithdraw} onClose={() => setOpenWithdraw(false)}>
        <DialogTitle>Withdraw Funds</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <TextField
            autoFocus
            margin="dense"
            label="Amount"
            type="number"
            fullWidth
            variant="outlined"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            inputProps={{ step: "0.01", min: "0.01", max: summary?.current_amount }}
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Available balance: ${summary?.current_amount.toFixed(2)}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenWithdraw(false)}>Cancel</Button>
          <Button 
            onClick={handleWithdraw} 
            variant="contained"
            disabled={withdrawMutation.isLoading}
          >
            Withdraw
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};