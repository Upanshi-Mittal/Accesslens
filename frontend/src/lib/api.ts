import axios from 'axios';
import { 
  AuditReport, 
  Engine, 
  StartAuditResponse, 
  AuditStatusResponse,
  AuditRequest 
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor for logging
apiClient.interceptors.request.use((config) => {
  if (process.env.NODE_ENV === 'development') {
    console.log(`Request to: ${config.url}`);
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const message = error.response.data?.detail || error.response.data?.message || 'An error occurred';
      
      switch (error.response.status) {
        case 400:
          throw new Error(`Bad request: ${message}`);
        case 422:
          throw new Error(`Validation error: ${message}`);
        case 429:
          throw new Error('Rate limit exceeded. Please wait a moment.');
        case 500:
          throw new Error('Server error. Please try again later.');
        default:
          throw new Error(message);
      }
    } else if (error.request) {
      throw new Error('No response from server. Please check your connection.');
    } else {
      throw new Error(`Request failed: ${error.message}`);
    }
  }
);

export const auditService = {
  // Health check - root endpoint
  health: async () => {
    // Health is usually at root /health, not /api/v1/health
    const response = await axios.get(`${API_BASE_URL.replace('/api/v1', '')}/health`);
    return response.data;
  },

  // Start audit
  startAudit: async (request: AuditRequest): Promise<StartAuditResponse> => {
    const response = await apiClient.post('/audit', {
      url: request.url,
      engines: request.engines || ['wcag_deterministic', 'structural_engine', 'contrast_engine'],
      enable_ai: request.enable_ai || false,
      depth: request.depth || 'standard',
      viewport: request.viewport || { width: 1280, height: 720 },
      wait_for_network_idle: request.wait_for_network_idle ?? true
    });
    return response.data;
  },

  // Get audit status
  getAuditStatus: async (auditId: string): Promise<AuditStatusResponse> => {
    const response = await apiClient.get(`/audit/${auditId}/status`);
    return response.data;
  },

  // Get audit results
  getAuditResults: async (auditId: string): Promise<AuditReport> => {
    const response = await apiClient.get(`/audit/${auditId}`);
    return response.data;
  },

  // List engines
  getEngines: async (): Promise<Engine[]> => {
    const response = await apiClient.get('/engines');
    return response.data;
  },

  // List recent audits
  listAudits: async (limit: number = 20, offset: number = 0): Promise<AuditReport[]> => {
    const response = await apiClient.get('/audit', {
      params: { limit, offset }
    });
    return response.data;
  },

  // Cancel audit
  cancelAudit: async (auditId: string): Promise<{ status: string; audit_id: string }> => {
    const response = await apiClient.post(`/audit/${auditId}/cancel`);
    return response.data;
  }
};

// Backwards compatibility alias
export const api = auditService;

