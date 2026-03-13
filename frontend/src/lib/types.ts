// Issue severity levels
export type IssueSeverity = 'critical' | 'serious' | 'moderate' | 'minor';

// Issue sources (engines)
export type IssueSource = 
  | 'wcag_deterministic' 
  | 'structural' 
  | 'contrast' 
  | 'ai_contextual' 
  | 'heuristic';

export type WCAGLevel = 'A' | 'AA' | 'AAA';

// Confidence levels
export type ConfidenceLevel = 'high' | 'medium' | 'low' | 'probabilistic';

// WCAG criteria
export interface WCAGCriteria {
  id: string;
  level: WCAGLevel;
  title: string;
  description?: string;
  url?: string;
}

// Element location in DOM
export interface ElementLocation {
  selector: string;
  xpath?: string;
  html?: string;
  node_index?: number;
  iframe_index?: number;
  shadow_root_path?: string[];
  bounding_box?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

// Remediation suggestion
export interface RemediationSuggestion {
  description: string;
  code_before?: string;
  code_after?: string;
  estimated_effort?: 'low' | 'medium' | 'high' | 'unknown';
}

// Evidence data
export interface EvidenceData {
  screenshot?: string;
  computed_values?: Record<string, any>;
  ai_reasoning?: string;
}

// Main issue model
export interface UnifiedIssue {
  id: string;
  timestamp: string;
  title: string;
  description: string;
  issue_type: string;
  severity: IssueSeverity;
  confidence: ConfidenceLevel;
  confidence_score: number;
  source: IssueSource;
  wcag_criteria: WCAGCriteria[];
  location?: ElementLocation;
  actual_value?: string;
  expected_value?: string;
  remediation?: RemediationSuggestion;
  evidence?: EvidenceData;
  engine_name: string;
  engine_version?: string;
  tags: string[];
}

// Audit summary
export interface AuditSummary {
  total_issues: number;
  by_severity: Record<IssueSeverity, number>;
  by_source: Record<IssueSource, number>;
  by_wcag_level: Record<string, number>;
  score: number;
  confidence_avg: number;
  coverage_comparator?: Record<string, any>;
}

// Audit request
export interface AuditRequest {
  url: string;
  engines?: string[];
  enable_ai?: boolean;
  depth?: 'quick' | 'standard' | 'deep';
  viewport?: {
    width: number;
    height: number;
  };
  wait_for_network_idle?: boolean;
}

// Audit report
export interface AuditReport {
  id: string;
  request: AuditRequest;
  timestamp: string;
  summary: AuditSummary;
  issues: UnifiedIssue[];
  accessibility_tree?: {
    nodes: any[];
    node_count: number;
  };
  metadata: Record<string, any>;
}

// Engine info
export interface Engine {
  name: string;
  version: string;
  capabilities: string[];
}

// API responses
export interface StartAuditResponse {
  audit_id: string;
  status: 'started';
  url: string;
}

export interface AuditStatusResponse {
  audit_id: string;
  status: 'in_progress' | 'completed';
  summary?: AuditSummary;
}

// Utility function to group issues
export function groupIssuesByEngine(issues: UnifiedIssue[]): Record<string, UnifiedIssue[]> {
  return issues.reduce((acc, issue) => {
    const engine = issue.engine_name;
    if (!acc[engine]) acc[engine] = [];
    acc[engine].push(issue);
    return acc;
  }, {} as Record<string, UnifiedIssue[]>);
}

export function groupIssuesBySeverity(issues: UnifiedIssue[]): Record<IssueSeverity, UnifiedIssue[]> {
  return issues.reduce((acc, issue) => {
    const severity = issue.severity;
    if (!acc[severity]) acc[severity] = [];
    acc[severity].push(issue);
    return acc;
  }, {} as Record<IssueSeverity, UnifiedIssue[]>);
}
