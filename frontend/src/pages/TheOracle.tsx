import React, { useState } from 'react';
import {
    Box,
    Typography,
    TextField,
    Button,
    Paper,
    Card,
    CardContent,
    CircularProgress,
    Alert,
    Avatar,
    Stack
} from '@mui/material';
import { AutoAwesome, Send, SmartToy, Warning, CheckCircle, Error as ErrorIcon } from '@mui/icons-material';
import { aiAPI } from '../services/api';

interface OracleResponse {
    status: string;
    message?: string;
    match_info?: string;
    verdict?: {
        color: string;
        title: string;
        text: string;
        confidence: number;
        ai_prediction: string;
        reasoning: string[];
    };
}

export const TheOracle: React.FC = () => {
    const [query, setQuery] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [response, setResponse] = useState<OracleResponse | null>(null);
    const [error, setError] = useState('');

    const handleAsk = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setIsLoading(true);
        setError('');
        setResponse(null);

        try {
            const res = await aiAPI.askOracle(query);
            setResponse(res.data);
        } catch (err) {
            console.error(err);
            setError('The Oracle is momentarily silent (Server Error). Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box p={3} maxWidth="800px" mx="auto">
            <Box textAlign="center" mb={6}>
                <Avatar sx={{ width: 80, height: 80, bgcolor: 'secondary.main', mx: 'auto', mb: 2 }}>
                    <AutoAwesome fontSize="large" />
                </Avatar>
                <Typography variant="h3" component="h1" gutterBottom fontWeight="bold">
                    The Oracle
                </Typography>
                <Typography variant="h6" color="text.secondary">
                    "Validate your gut feeling with Data Science."
                </Typography>
                <Typography variant="body1" color="text.secondary" mt={1}>
                    Ask me anything like: <i>"Is it safe to bet on Real Madrid today?"</i>
                </Typography>
            </Box>

            <Paper elevation={4} sx={{ p: 2, mb: 4, borderRadius: 2 }}>
                <form onSubmit={handleAsk}>
                    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                        <TextField
                            fullWidth
                            variant="outlined"
                            placeholder="Ask the Oracle..."
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            disabled={isLoading}
                        />
                        <Button
                            variant="contained"
                            size="large"
                            endIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <Send />}
                            type="submit"
                            disabled={isLoading || !query}
                            sx={{ minWidth: '120px', borderRadius: 2 }}
                        >
                            Ask
                        </Button>
                    </Stack>
                </form>
            </Paper>

            {error && <Alert severity="error">{error}</Alert>}

            {response && (
                <Box sx={{ animation: 'fadeIn 0.5s' }}>
                    {response.status === 'success' && response.verdict ? (
                        <Card 
                            elevation={6} 
                            sx={{ 
                                borderLeft: 8, 
                                borderColor: 
                                    response.verdict.color === 'green' ? 'success.main' : 
                                    response.verdict.color === 'red' ? 'error.main' : 'warning.main' 
                            }}
                        >
                            <CardContent sx={{ p: 4 }}>
                                <Box display="flex" alignItems="center" mb={2}>
                                    {response.verdict.color === 'green' ? <CheckCircle color="success" fontSize="large" sx={{ mr: 2 }} /> :
                                     response.verdict.color === 'red' ? <ErrorIcon color="error" fontSize="large" sx={{ mr: 2 }} /> :
                                     <Warning color="warning" fontSize="large" sx={{ mr: 2 }} />}
                                    
                                    <Typography variant="h4">
                                        {response.verdict.title}
                                    </Typography>
                                </Box>
                                
                                <Typography variant="subtitle1" color="text.secondary" gutterBottom>
                                    Match: {response.match_info}
                                </Typography>
                                
                                <Typography variant="h6" paragraph sx={{ mt: 2, fontWeight: 'medium' }}>
                                    {response.verdict.text}
                                </Typography>

                                <Box bgcolor="grey.50" p={2} borderRadius={2} mt={3}>
                                    <Typography variant="subtitle2" gutterBottom>
                                        <SmartToy fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
                                        AI Analysis
                                    </Typography>
                                    <ul>
                                        {response.verdict.reasoning.map((r, idx) => (
                                            <li key={idx}>
                                                <Typography variant="body2">{r}</Typography>
                                            </li>
                                        ))}
                                    </ul>
                                </Box>
                            </CardContent>
                        </Card>
                    ) : (
                        <Alert severity="warning" icon={<Warning fontSize="inherit" />}>
                            {response.message || "I couldn't understand that request."}
                        </Alert>
                    )}
                </Box>
            )}
        </Box>
    );
};
