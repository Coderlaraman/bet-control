import React from 'react';
import { useQuery } from 'react-query';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Grid,
    Chip,
    CircularProgress,
    Alert,
    Divider,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Paper
} from '@mui/material';
import {
    SportsSoccer,
    TrendingUp,
    EmojiEvents,
    Timeline,
    Psychology
} from '@mui/icons-material';
import axios from 'axios';

interface MatchStats {
    wins_last_5: number;
    goals_avg: number;
    conceded_avg: number;
}

interface Prediction {
    id: string;
    sport: string;
    league: string;
    home_team: string;
    away_team: string;
    date: string;
    prediction: string;
    confidence_score: number;
    reasoning: string[];
    suggested_odds: number;
    home_stats: MatchStats;
    away_stats: MatchStats;
}

const fetchPredictions = async () => {
    // In production, use environment variable for API URL
    const response = await axios.get('http://localhost:8075/api/v1/ai/suggestions');
    return response.data;
};

export const AIPredictions: React.FC = () => {
    const { data: predictions, isLoading, error } = useQuery<Prediction[]>(
        'aiPredictions',
        fetchPredictions
    );

    if (isLoading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Box p={3}>
                <Alert severity="error">
                    Error loading AI predictions. Please try again later.
                </Alert>
            </Box>
        );
    }

    return (
        <Box p={3}>
            <Box mb={4} display="flex" alignItems="center" gap={2}>
                <Psychology fontSize="large" color="primary" />
                <Box>
                    <Typography variant="h4" component="h1" gutterBottom>
                        AI Betting Intelligence
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary">
                        Daily high-confidence betting suggestions powered by statistical analysis
                    </Typography>
                </Box>
            </Box>

            <Grid container spacing={3}>
                {predictions?.map((prediction) => (
                    <Grid item xs={12} md={6} lg={4} key={prediction.id}>
                        <Card
                            elevation={3}
                            sx={{
                                height: '100%',
                                display: 'flex',
                                flexDirection: 'column',
                                position: 'relative',
                                overflow: 'visible'
                            }}
                        >
                            <Box
                                position="absolute"
                                top={-10}
                                right={-10}
                                zIndex={1}
                            >
                                <Chip
                                    label={`${(prediction.confidence_score * 100).toFixed(0)}% Confidence`}
                                    color={prediction.confidence_score > 0.8 ? "success" : "primary"}
                                    icon={<TrendingUp />}
                                />
                            </Box>

                            <CardContent>
                                <Box display="flex" alignItems="center" mb={2}>
                                    <SportsSoccer color="action" sx={{ mr: 1 }} />
                                    <Typography variant="overline" color="text.secondary">
                                        {prediction.league}
                                    </Typography>
                                </Box>

                                <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                                    <Box textAlign="center" flex={1}>
                                        <Typography variant="h6">{prediction.home_team}</Typography>
                                    </Box>
                                    <Box px={2}>
                                        <Typography variant="h5" color="text.secondary">VS</Typography>
                                    </Box>
                                    <Box textAlign="center" flex={1}>
                                        <Typography variant="h6">{prediction.away_team}</Typography>
                                    </Box>
                                </Box>

                                <Paper variant="outlined" sx={{ p: 2, mb: 2, bgcolor: 'primary.main', color: 'white' }}>
                                    <Typography variant="subtitle2" align="center" gutterBottom>
                                        RECOMMENDED BET
                                    </Typography>
                                    <Typography variant="h5" align="center" fontWeight="bold">
                                        {prediction.prediction}
                                    </Typography>
                                    <Typography variant="caption" display="block" align="center" sx={{ mt: 1 }}>
                                        Suggested Odds: {prediction.suggested_odds}
                                    </Typography>
                                </Paper>

                                <Divider sx={{ my: 2 }} />

                                <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                                    <Timeline sx={{ mr: 1, fontSize: 20 }} />
                                    Analysis & Reasoning
                                </Typography>

                                <List dense>
                                    {prediction.reasoning.map((reason, idx) => (
                                        <ListItem key={idx} disablePadding sx={{ mb: 1 }}>
                                            <ListItemIcon sx={{ minWidth: 30 }}>
                                                <EmojiEvents fontSize="small" color="warning" />
                                            </ListItemIcon>
                                            <ListItemText primary={reason} />
                                        </ListItem>
                                    ))}
                                </List>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}

                {predictions?.length === 0 && (
                    <Grid item xs={12}>
                        <Alert severity="info">
                            No high-confidence predictions found for today's matches. Check back later!
                        </Alert>
                    </Grid>
                )}
            </Grid>
        </Box>
    );
};
