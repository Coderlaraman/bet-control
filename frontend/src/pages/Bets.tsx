import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { betsAPI } from '../services/api';

export const Bets: React.FC = () => {
  const navigate = useNavigate();
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedBet, setSelectedBet] = useState<any>(null);
  const [openDialog, setOpenDialog] = useState(false);

  const { data: bets, isLoading, error, refetch } = useQuery(
    ['bets', filterStatus],
    () => betsAPI.getBets({ status: filterStatus !== 'all' ? filterStatus : undefined }).then(res => res.data)
  );

  const handleViewBet = (bet: any) => {
    setSelectedBet(bet);
    setOpenDialog(true);
  };

  const handleEditBet = (betId: number) => {
    navigate(`/bets/edit/${betId}`);
  };

  const handleDeleteBet = async (betId: number) => {
    if (window.confirm('Are you sure you want to delete this bet?')) {
      try {
        await betsAPI.deleteBet(betId);
        refetch();
      } catch (error) {
        console.error('Error deleting bet:', error);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'won':
        return 'success';
      case 'lost':
        return 'error';
      case 'pending':
        return 'warning';
      case 'void':
        return 'default';
      default:
        return 'primary';
    }
  };

  if (isLoading) {
    return <Typography>Loading bets...</Typography>;
  }

  if (error) {
    return <Typography color="error">Error loading bets</Typography>;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Bets Management</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/bets/new')}
        >
          New Bet
        </Button>
      </Box>

      <Box sx={{ mb: 3 }}>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Filter by Status</InputLabel>
          <Select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            label="Filter by Status"
          >
            <MenuItem value="all">All Bets</MenuItem>
            <MenuItem value="pending">Pending</MenuItem>
            <MenuItem value="won">Won</MenuItem>
            <MenuItem value="lost">Lost</MenuItem>
            <MenuItem value="void">Void</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Event</TableCell>
              <TableCell>Sport</TableCell>
              <TableCell>Market</TableCell>
              <TableCell>Pick</TableCell>
              <TableCell>Odds</TableCell>
              <TableCell>Stake</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Result</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {bets?.map((bet: any) => (
              <TableRow key={bet.id}>
                <TableCell>{new Date(bet.created_at).toLocaleDateString()}</TableCell>
                <TableCell>{bet.event_name}</TableCell>
                <TableCell>{bet.sport?.name || 'N/A'}</TableCell>
                <TableCell>{bet.market?.name || 'N/A'}</TableCell>
                <TableCell>{bet.bet_description}</TableCell>
                <TableCell>{bet.odds}</TableCell>
                <TableCell>${Number(bet.stake).toFixed(2)}</TableCell>
                <TableCell>
                  <Chip
                    label={bet.status}
                    color={getStatusColor(bet.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {bet.result_amount ? `$${Number(bet.result_amount).toFixed(2)}` : '-'}
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => handleViewBet(bet)}
                    title="View Details"
                  >
                    <ViewIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleEditBet(bet.id)}
                    title="Edit Bet"
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteBet(bet.id)}
                    title="Delete Bet"
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Bet Details Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Bet Details</DialogTitle>
        <DialogContent>
          {selectedBet && (
            <Box>
              <Typography><strong>Event:</strong> {selectedBet.event_name}</Typography>
              <Typography><strong>Date:</strong> {new Date(selectedBet.event_date).toLocaleDateString()}</Typography>
              <Typography><strong>Sport:</strong> {selectedBet.sport?.name || 'N/A'}</Typography>
              <Typography><strong>League:</strong> {selectedBet.league?.name || 'N/A'}</Typography>
              <Typography><strong>Market:</strong> {selectedBet.market?.name || 'N/A'}</Typography>
              <Typography><strong>Pick:</strong> {selectedBet.bet_description}</Typography>
              <Typography><strong>Odds:</strong> {selectedBet.odds}</Typography>
              <Typography><strong>Stake:</strong> ${Number(selectedBet.stake).toFixed(2)}</Typography>
              <Typography><strong>Potential Win:</strong> ${Number(selectedBet.potential_win).toFixed(2)}</Typography>
              <Typography><strong>Status:</strong> {selectedBet.status}</Typography>
              {selectedBet.result_amount && (
                <Typography><strong>Result Amount:</strong> ${Number(selectedBet.result_amount).toFixed(2)}</Typography>
              )}
              {selectedBet.notes && (
                <Typography><strong>Notes:</strong> {selectedBet.notes}</Typography>
              )}
              {selectedBet.bet_slip_id && (
                <Typography><strong>Bet Slip ID:</strong> {selectedBet.bet_slip_id}</Typography>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};