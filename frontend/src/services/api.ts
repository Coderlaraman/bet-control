import axios from 'axios';
import Cookies from 'js-cookie';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8075/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = Cookies.get('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth data and redirect to login
      Cookies.remove('access_token');
      Cookies.remove('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface LoginData {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Bet {
  id: number;
  user_id: number;
  bet_type_id: number;
  sport_id: number;
  country_id?: number;
  league_id?: number;
  market_id?: number;
  event_name: string;
  event_date: string;
  event_time?: string;
  home_team?: string;
  away_team?: string;
  bet_description: string;
  odds: number;
  stake: number;
  potential_win: number;
  status: 'pending' | 'won' | 'lost' | 'void' | 'half_won' | 'half_lost';
  result_amount?: number;
  settled_at?: string;
  bet_slip_id?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface BetCreate {
  bet_type_id: number;
  sport_id: number;
  country_id?: number;
  league_id?: number;
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

export interface BankrollSummary {
  current_amount: number;
  initial_amount: number;
  profit_loss: number;
  max_bet_allowed: number;
  min_bet_amount: number;
  max_bet_amount: number;
  max_bet_percentage: number;
  currency: string;
  recent_transactions: BankrollTransaction[];
}

export interface BankrollTransaction {
  type: string;
  amount: number;
  balance_before: number;
  balance_after: number;
  created_at: string;
}

export interface BettingStats {
  total_bets: number;
  won_bets: number;
  lost_bets: number;
  void_bets: number;
  pending_bets: number;
  total_staked: number;
  total_won: number;
  total_profit: number;
  win_rate: number;
  roi: number;
}

// Auth API
export const authAPI = {
  login: (data: LoginData) => {
    // Enviar JSON en lugar de form-urlencoded
    return api.post<AuthResponse>('/auth/login', data);
  },
  register: (data: any) => api.post('/auth/register', data),
  refresh: (refreshToken: string) => api.post<AuthResponse>('/auth/refresh', { refresh_token: refreshToken }),
};

// Bets API
export const betsAPI = {
  getBets: (params?: any) => api.get<Bet[]>('/bets', { params }),
  getBet: (id: number) => api.get<Bet>(`/bets/${id}`),
  createBet: (data: BetCreate) => api.post<Bet>('/bets', data),
  updateBet: (id: number, data: Partial<Bet>) => api.put<Bet>(`/bets/${id}`, data),
  deleteBet: (id: number) => api.delete(`/bets/${id}`),
  getBettingStats: () => api.get<BettingStats>('/bets/summary/stats'),
  parseBet: (text: string) => api.post<any>('/bets/smart-entry', { text }),
};

// Bankroll API
export const bankrollAPI = {
  getSummary: () => api.get<BankrollSummary>('/bankroll/summary'),
  updateConfig: (data: any) => api.put('/bankroll/config', data),
  deposit: (data: { amount: number }) => api.post('/bankroll/deposit', data),
  withdraw: (data: { amount: number }) => api.post('/bankroll/withdraw', data),
};

// AI API
export const aiAPI = {
  getSuggestions: () => api.get('/ai/suggestions'),
  getDavidGoliath: () => api.get('/ai-modules/david-goliath'),
  askOracle: (query: string) => api.post('/ai-modules/oracle/ask', { query }),
};

export default api;