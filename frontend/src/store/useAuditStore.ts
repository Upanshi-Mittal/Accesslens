import { create } from 'zustand';
import { auditService } from '../lib/api';
import { 
  AuditReport, 
  AuditSummary, 
  Engine, 
  AuditRequest,
  AuditStatusResponse 
} from '../lib/types';

interface AuditState {
  recentAudits: any[]; // Changed from AuditSummary[] as list_reports returns simplified records
  activeAudit: AuditStatusResponse | AuditReport | null;
  engines: Engine[];
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchEngines: () => Promise<void>;
  fetchRecentAudits: () => Promise<void>;
  startNewAudit: (request: AuditRequest) => Promise<void>;
  pollAuditStatus: (auditId: string) => Promise<void>;
  setActiveAudit: (audit: AuditStatusResponse | AuditReport | null) => void;
  setError: (error: string | null) => void;
}

export const useAuditStore = create<AuditState>((set, get) => ({
  recentAudits: [],
  activeAudit: null,
  engines: [],
  isLoading: false,
  error: null,

  setActiveAudit: (audit) => set({ activeAudit: audit }),
  setError: (error) => set({ error }),

  fetchEngines: async () => {
    set({ isLoading: true });
    try {
      const engines = await auditService.getEngines();
      set({ engines, isLoading: false });
    } catch (err: any) {
      set({ error: 'Failed to fetch engines', isLoading: false });
    }
  },

  fetchRecentAudits: async () => {
    set({ isLoading: true });
    try {
      const audits = await auditService.listAudits();
      set({ recentAudits: audits, isLoading: false });
    } catch (err: any) {
      set({ isLoading: false });
    }
  },

  startNewAudit: async (request) => {
    set({ isLoading: true, error: null });
    try {
      const response = await auditService.startAudit(request);
      // We don't have the full report yet, just the start response
      set({ 
        activeAudit: { audit_id: response.audit_id, status: 'in_progress' }, 
        isLoading: false 
      });
      // Start polling
      get().pollAuditStatus(response.audit_id);
    } catch (err: any) {
      set({ error: err.message || 'Failed to start audit', isLoading: false });
    }
  },

  pollAuditStatus: async (auditId) => {
    const poll = async () => {
      try {
        const audit = await auditService.getAuditStatus(auditId);
        set({ activeAudit: audit });
        
        // Use string literal perfectly matching types
        if (audit.status === 'completed') {
          // If completed, fetch full results
          const results = await auditService.getAuditResults(auditId);
          set({ activeAudit: results });
          get().fetchRecentAudits();
          return;
        }
        
        if (audit.status === ('failed' as any) || audit.status === ('cancelled' as any)) {
          get().fetchRecentAudits();
          return;
        }
        
        // Continue polling if still in progress
        setTimeout(poll, 2000);
      } catch (err) {
        console.error('Polling failed', err);
      }
    };
    
    poll();
  },
}));
