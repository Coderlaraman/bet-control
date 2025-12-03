import React, { useState } from 'react';
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
    Paper,
    Tabs,
    Tab,
    Button
} from '@mui/material';
import {
    SportsSoccer,
    TrendingUp,
    EmojiEvents,
    Timeline,
    Psychology,
    LocalFireDepartment
} from '@mui/icons-material';
import { aiAPI } from '../services/api';

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

interface DavidGoliathOpp {
    match_id: number;
    date: string;
    league: string;
    home_team: string;
    away_team: string;
    type: string;
    analysis: {
        goliath: string;
        david: string;
        scenario: string;
        details: string;
        confidence: number;
        recommendation: string;
    };
    confidence: number;
}

const fetchPredictions = async () => {
    const response = await aiAPI.getSuggestions();
    return response.data;
};

const fetchDavidGoliath = async () => {
    const response = await aiAPI.getDavidGoliath();
    return response.data;
};

export const AIPredictions: React.FC = () => {
    const [tabValue, setTabValue] = useState(0);

    const { data: predictions, isLoading: loadingPreds, error: errorPreds } = useQuery<Prediction[]>(
        'aiPredictions',
        fetchPredictions
    );

    const { data: dgOpps, isLoading: loadingDG, error: errorDG } = useQuery<DavidGoliathOpp[]>(
        'davidGoliath',
        fetchDavidGoliath
    );

    const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
        setTabValue(newValue);
    };

    const isLoading = loadingPreds || loadingDG;
    const error = errorPreds || errorDG;

    if (isLoading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
                <CircularProgress />
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
                        Advanced analytics and mismatch detection
                    </Typography>
                </Box>
            </Box>

            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
                <Tabs value={tabValue} onChange={handleTabChange}>
                    <Tab label="Daily Predictions" />
                    <Tab label="David vs Goliath (Value)" icon={<LocalFireDepartment color={dgOpps?.length ? "error" : "disabled"} />} iconPosition="end" />
                </Tabs>
            </Box>

            {tabValue === 0 && (
                <Grid container spacing={3}>
                    <>
                        {errorPreds && (
                            <Grid item xs={12}>
                                <Alert severity="error">Error loading daily predictions.</Alert>
                            </Grid>
                        )}
                        {(predictions || []).map((prediction) => (
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
                        {predictions?.length === 0 && !errorPreds && (
                            <Grid item xs={12}>
                                <Alert severity="info">
                                    No high-confidence predictions found for today's matches. Check "David vs Goliath" tab!
                                </Alert>
                            </Grid>
                        )}
                    </>
                </Grid>
            )}

            {tabValue === 1 && (
                <Grid container spacing={3}>
                    <>
                        {errorDG && (
                            <Grid item xs={12}>
                                <Alert severity="error">Error loading value opportunities.</Alert>
                            </Grid>
                        )}
                        {(dgOpps || []).length === 0 && (
                            <Grid item xs={12}>
                                <Alert severity="info">No "David vs Goliath" mismatches detected in upcoming games.</Alert>
                            </Grid>
                        )}
                        {(dgOpps || []).map((opp) => (
                            <Grid item xs={12} md={6} key={opp.match_id}>
                                <Card elevation={4} sx={{ borderLeft: 6, borderColor: 'error.main' }}>
                                    <CardContent>
                                        <Box display="flex" justifyContent="space-between" alignItems="start">
                                            <Box>
                                                <Chip label={opp.analysis.scenario} color="error" size="small" sx={{ mb: 1 }} />
                                                <Typography variant="h6">
                                                    {opp.home_team} vs {opp.away_team}
                                                </Typography>
                                                <Typography variant="body2" color="text.secondary">
                                                    {new Date(opp.date).toLocaleDateString()} - {opp.league}
                                                </Typography>
                                            </Box>
                                            <Box textAlign="right">
                                                <Typography variant="h4" color="success.main" fontWeight="bold">
                                                    {(opp.confidence * 100).toFixed(0)}%
                                                </Typography>
                                                <Typography variant="caption">Confidence</Typography>
                                            </Box>
                                        </Box>
                                        
                                        <Paper sx={{ bgcolor: 'grey.100', p: 2, mt: 2 }}>
                                            <Typography variant="body1" fontWeight="medium">
                                                🚀 {opp.analysis.recommendation}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                                {opp.analysis.details}
                                            </Typography>
                                        </Paper>
                                    </CardContent>
                                </Card>
                            </Grid>
                        ))}
                    </>
                </Grid>
            )}
        </Box>
    );
};
