/**
 * mockData.ts
 * Mock data for the Regulatory Assistant app (P7-REG).
 * Used when P6-REG agent, P0-DATAGEN-REG, and P1-REG are not yet deployed.
 *
 * Q&A pairs are grounded in corrected FCC 26-19 facts from BUILD-PLAN.md §0.
 * All data is SYNTHETIC — for demo scaffolding only.
 */

// --- Feature flag: set to false to use live agent + SQL queries ---
export const USE_MOCK_DATA = true;

// --- Types ---

export interface Citation {
  id: number;
  document_title: string;
  paragraph_ref: string;
  effective_date: string;
  jurisdiction: string;
  excerpt: string;
  confidence: 'high' | 'medium' | 'low';
  doc_id: string;
}

export interface AgentQA {
  id: number;
  question: string;
  answer: string;
  citations: Citation[];
}

export interface JurisdictionRow {
  state: string;
  state_name: string;
  federal_regulator: string;
  state_puc: string;
  notice_period_days: number;
  filing_type: string;
  section_214_required: boolean;
  residential_notice_days: number;
  compliance_status: 'clear' | 'pending' | 'blocked' | 'overdue';
  pending_filings: number;
  next_deadline: string;
}

export interface ChecklistItem {
  id: string;
  state: string;
  wire_center: string;
  requirement: string;
  requirement_type: 'section_214' | 'state_puc' | 'residential_notice' | '911_coordination' | 'environmental';
  status: 'complete' | 'pending' | 'overdue' | 'blocked' | 'flagged';
  due_date: string;
  completed_date: string | null;
  notes: string;
}

export interface RegDocument {
  doc_id: string;
  title: string;
  document_type: 'fcc_order' | 'puc_docket' | 'notice_template' | 'guidance' | 'legislative';
  issuing_body: string;
  jurisdiction: string;
  effective_date: string;
  effective_end_date: string | null;
  keywords: string[];
  summary: string;
}

export interface RegKPIs {
  jurisdictions_covered: number;
  pending_filings: number;
  days_until_next_deadline: number;
  compliance_pct: number;
  overdue_items: number;
  documents_indexed: number;
}

export type ActiveTab = 'ask' | 'jurisdiction' | 'checklist' | 'documents';

// --- Mock Q&A Pairs (grounded in FCC 26-19 corrections from BUILD-PLAN.md §0) ---

const MOCK_QA: AgentQA[] = [
  {
    id: 1,
    question: 'What is Section 214?',
    answer: 'Section 214(a) of the Communications Act requires carriers to obtain FCC authorization before discontinuing, reducing, or impairing telecommunications service. Under FCC 26-19, the Section 214(a) discontinuance process has been streamlined with a consolidated tech-transition rule, 31-day automatic grants for qualifying applications, and blanket grandfathering authority. However, Section 214 authorization is still required when a copper retirement causes a service discontinuance.',
    citations: [
      { id: 1, document_title: 'FCC 26-19: Accelerating Wireline Broadband Deployment', paragraph_ref: 'para. 47-52', effective_date: '2026-04-15', jurisdiction: 'Federal', excerpt: 'The Commission adopts a consolidated tech-transition discontinuance rule that streamlines the Section 214(a) process with 31-day automatic grants for qualifying applications...', confidence: 'high', doc_id: 'FCC-26-19' },
    ],
  },
  {
    id: 2,
    question: 'Do we still need Section 214 authorization?',
    answer: 'YES — Section 214(a) authorization is still required when copper retirement causes a service discontinuance. FCC 26-19 eliminated the Section 251(c)(5) network-change disclosure FCC filing and its public-notice/objection process, NOT Section 214. The streamlined process includes 31-day automatic grants and blanket grandfathering, but the authorization requirement itself remains.',
    citations: [
      { id: 2, document_title: 'FCC 26-19: Accelerating Wireline Broadband Deployment', paragraph_ref: 'para. 23-31', effective_date: '2026-04-15', jurisdiction: 'Federal', excerpt: 'The Commission eliminates the Section 251(c)(5) network-change disclosure filing requirement for copper retirements while preserving the Section 214(a) discontinuance authorization...', confidence: 'high', doc_id: 'FCC-26-19' },
    ],
  },
  {
    id: 3,
    question: 'What notice do we give residential customers?',
    answer: '90-day direct notice to affected residential customers is required. This requirement remains intact under the streamlined FCC 26-19 rules. The notice must be sent via mail or other direct communication to each affected residential subscriber at least 90 days before the planned copper retirement date.',
    citations: [
      { id: 3, document_title: 'FCC 26-19: Accelerating Wireline Broadband Deployment', paragraph_ref: 'para. 55-58', effective_date: '2026-04-15', jurisdiction: 'Federal', excerpt: 'The 90-day residential direct-notice requirement is retained. Carriers must provide written notice to each affected residential subscriber...', confidence: 'high', doc_id: 'FCC-26-19' },
      { id: 4, document_title: '47 CFR §63.71 — Discontinuance Notice Requirements', paragraph_ref: '§63.71(a)', effective_date: '2026-04-15', jurisdiction: 'Federal', excerpt: 'Each carrier proposing to discontinue service shall give notice to all affected subscribers at least 90 days prior...', confidence: 'high', doc_id: '47CFR-63-71' },
    ],
  },
  {
    id: 4,
    question: 'What changed with FCC 26-19?',
    answer: 'FCC 26-19 (March 2026) made four major changes: (1) Eliminated Section 251(c)(5) network-change FCC filing and its public-notice/objection process for copper retirement. (2) Streamlined Section 214(a) discontinuance: consolidated tech-transition rule with 31-day automatic grants. (3) Added blanket grandfathering authority for qualifying retirements. (4) Added 911 coordination requirement — carriers must notify PSAPs before retiring copper in an area. Note: Section 214 authorization is still required when retirement causes service discontinuance.',
    citations: [
      { id: 5, document_title: 'FCC 26-19: Accelerating Wireline Broadband Deployment', paragraph_ref: 'Full order', effective_date: '2026-04-15', jurisdiction: 'Federal', excerpt: 'This Report and Order accelerates wireline broadband deployment by eliminating the Section 251(c)(5) network-change disclosure requirements and streamlining Section 214(a) discontinuance...', confidence: 'high', doc_id: 'FCC-26-19' },
    ],
  },
  {
    id: 5,
    question: "What are Colorado's requirements?",
    answer: "Colorado PUC (CPUC) requires 90-day advance notice aligned with the federal baseline: (1) CPUC filing with broadband availability certification demonstrating replacement service meets or exceeds retired service in the retirement area. (2) Rural service continuity plan for areas with limited alternatives. (3) Lifeline program transition coordination for low-income subscribers. (4) No separate state environmental review (unlike some states).",
    citations: [
      { id: 6, document_title: 'CPUC Rule 4 CCR 723-2: Copper Retirement Procedures', paragraph_ref: 'Section III.A', effective_date: '2025-01-15', jurisdiction: 'Colorado', excerpt: 'The Commission requires carriers to file notice at least 90 days before planned copper retirement, with broadband availability certification demonstrating adequate replacement service...', confidence: 'medium', doc_id: 'CPUC-4CCR' },
    ],
  },
  {
    id: 6,
    question: '911 coordination requirements?',
    answer: 'FCC 26-19 added a 911 coordination requirement for copper retirements. Carriers must: (1) Notify all Public Safety Answering Points (PSAPs) in the affected area. (2) Coordinate with 911 authorities to ensure continuity of emergency services during and after the transition. (3) Document the coordination in the Section 214 application. This was a new addition to the streamlined rules.',
    citations: [
      { id: 7, document_title: 'FCC 26-19: Accelerating Wireline Broadband Deployment', paragraph_ref: 'para. 62-67', effective_date: '2026-04-15', jurisdiction: 'Federal', excerpt: 'Carriers must coordinate with 911 authorities and PSAPs in the affected area before retiring copper infrastructure to ensure continuity of emergency communications...', confidence: 'high', doc_id: 'FCC-26-19' },
    ],
  },
  {
    id: 7,
    question: "What's the timeline for copper retirement in Oregon?",
    answer: "Oregon PUC requires 120-day advance notice (longer than the federal 90-day minimum). Additional requirements: (1) Detailed service migration plan submitted with notice. (2) Demonstration that replacement service meets or exceeds retired service quality. (3) Public comment period of 30 days. (4) Rural area exemptions may require extended 180-day notice.",
    citations: [
      { id: 8, document_title: 'Oregon PUC AR 650: Telecommunications Service Retirement', paragraph_ref: 'Rule 860-032-0420', effective_date: '2024-07-01', jurisdiction: 'Oregon', excerpt: 'Telecommunications carriers shall provide 120 days advance written notice to the Commission and affected customers before discontinuing copper-based service...', confidence: 'medium', doc_id: 'OR-PUC-AR650' },
    ],
  },
  {
    id: 8,
    question: "What's different about Arizona?",
    answer: "Arizona Corporation Commission (ACC) has a lighter regulatory framework: (1) 60-day notice to ACC (shorter than federal requirement, so federal 90-day notice governs). (2) No separate state environmental review. (3) Carrier of Last Resort (COLR) obligations still apply in designated service areas. (4) Competitive areas have streamlined approval.",
    citations: [
      { id: 9, document_title: 'ACC Decision No. 79XXX: Wireline Service Modifications', paragraph_ref: 'Finding of Fact 12', effective_date: '2023-11-20', jurisdiction: 'Arizona', excerpt: 'In competitive service areas, carriers may modify or retire wireline infrastructure with 60-day notice to the Commission, provided replacement service is available...', confidence: 'medium', doc_id: 'ACC-79XXX' },
    ],
  },
  {
    id: 9,
    question: 'What are the penalties for non-compliance?',
    answer: 'Non-compliance with Section 214 requirements can result in: (1) FCC enforcement action including fines up to $100,000 per violation per day. (2) State PUC penalties vary by jurisdiction (CO: up to $50,000/day, OR: up to $10,000/day). (3) Forced service restoration if retirement proceeds without proper authorization. (4) Citizen complaints triggering formal FCC proceedings.',
    citations: [
      { id: 10, document_title: '47 U.S.C. §503(b): Forfeiture Penalties', paragraph_ref: '§503(b)(2)(B)', effective_date: '2021-01-01', jurisdiction: 'Federal', excerpt: 'Any person who willfully or repeatedly fails to comply with the provisions of this Act shall be liable for a forfeiture penalty...', confidence: 'high', doc_id: 'USC-47-503' },
    ],
  },
  {
    id: 10,
    question: 'How do we handle Lifeline subscribers?',
    answer: 'Lifeline subscribers require special handling during copper retirement: (1) Must be individually notified with language-accessible communications. (2) Migration to equivalent-or-better Lifeline service must be arranged at no cost to the subscriber. (3) Colorado requires Lifeline transition coordination with CPUC. (4) Federal Lifeline obligations continue regardless of technology transition.',
    citations: [
      { id: 11, document_title: 'FCC 26-19: Accelerating Wireline Broadband Deployment', paragraph_ref: 'para. 71-74', effective_date: '2026-04-15', jurisdiction: 'Federal', excerpt: 'Carriers must ensure that Lifeline-eligible subscribers maintain access to equivalent or superior service during and after technology transitions...', confidence: 'high', doc_id: 'FCC-26-19' },
    ],
  },
];

// --- Mock jurisdiction data (6 LEGACY_STATES from synthetic_assets.py) ---

const MOCK_JURISDICTIONS: JurisdictionRow[] = [
  { state: 'CO', state_name: 'Colorado', federal_regulator: 'FCC', state_puc: 'CPUC', notice_period_days: 90, filing_type: 'CPUC Filing + Section 214', section_214_required: true, residential_notice_days: 90, compliance_status: 'pending', pending_filings: 3, next_deadline: '2026-11-15' },
  { state: 'WA', state_name: 'Washington', federal_regulator: 'FCC', state_puc: 'WUTC', notice_period_days: 90, filing_type: 'Section 214', section_214_required: true, residential_notice_days: 90, compliance_status: 'clear', pending_filings: 0, next_deadline: '2027-01-20' },
  { state: 'OR', state_name: 'Oregon', federal_regulator: 'FCC', state_puc: 'Oregon PUC', notice_period_days: 120, filing_type: 'AR 650 + Section 214', section_214_required: true, residential_notice_days: 90, compliance_status: 'pending', pending_filings: 2, next_deadline: '2026-12-01' },
  { state: 'AZ', state_name: 'Arizona', federal_regulator: 'FCC', state_puc: 'ACC', notice_period_days: 90, filing_type: 'Section 214', section_214_required: true, residential_notice_days: 90, compliance_status: 'clear', pending_filings: 0, next_deadline: '2027-03-01' },
  { state: 'MN', state_name: 'Minnesota', federal_regulator: 'FCC', state_puc: 'MN PUC', notice_period_days: 90, filing_type: 'Section 214 + State Notice', section_214_required: true, residential_notice_days: 90, compliance_status: 'overdue', pending_filings: 1, next_deadline: '2026-09-01' },
  { state: 'ID', state_name: 'Idaho', federal_regulator: 'FCC', state_puc: 'IPUC', notice_period_days: 60, filing_type: 'Section 214', section_214_required: true, residential_notice_days: 90, compliance_status: 'clear', pending_filings: 0, next_deadline: '2027-06-15' },
];

// --- Mock compliance checklist ---

const MOCK_CHECKLIST: ChecklistItem[] = [
  { id: 'CO-WC001-214', state: 'CO', wire_center: 'Denver-Downtown', requirement: 'Section 214 application filed', requirement_type: 'section_214', status: 'pending', due_date: '2026-10-01', completed_date: null, notes: 'Application drafted, pending legal review' },
  { id: 'CO-WC001-CPUC', state: 'CO', wire_center: 'Denver-Downtown', requirement: 'CPUC filing with broadband certification', requirement_type: 'state_puc', status: 'pending', due_date: '2026-10-01', completed_date: null, notes: 'Waiting on Section 214 filing first' },
  { id: 'CO-WC001-NOTICE', state: 'CO', wire_center: 'Denver-Downtown', requirement: '90-day residential notice mailed', requirement_type: 'residential_notice', status: 'blocked', due_date: '2026-10-15', completed_date: null, notes: 'Blocked — customer list needs verification' },
  { id: 'CO-WC001-911', state: 'CO', wire_center: 'Denver-Downtown', requirement: 'PSAP coordination completed', requirement_type: '911_coordination', status: 'complete', due_date: '2026-09-01', completed_date: '2026-08-28', notes: 'Denver PD PSAP notified, acknowledgement received' },
  { id: 'CO-WC001-RURAL', state: 'CO', wire_center: 'Denver-Downtown', requirement: 'Rural service continuity plan', requirement_type: 'state_puc', status: 'pending', due_date: '2026-11-01', completed_date: null, notes: 'Broadband availability assessment in progress' },
  { id: 'OR-WC010-214', state: 'OR', wire_center: 'Portland-Central', requirement: 'Section 214 application filed', requirement_type: 'section_214', status: 'complete', due_date: '2026-09-15', completed_date: '2026-09-10', notes: '31-day auto-grant period started' },
  { id: 'OR-WC010-PUC', state: 'OR', wire_center: 'Portland-Central', requirement: 'Oregon PUC AR 650 notice', requirement_type: 'state_puc', status: 'pending', due_date: '2026-10-01', completed_date: null, notes: 'Service migration plan being prepared' },
  { id: 'OR-WC010-NOTICE', state: 'OR', wire_center: 'Portland-Central', requirement: '90-day residential notice mailed', requirement_type: 'residential_notice', status: 'pending', due_date: '2026-10-15', completed_date: null, notes: 'Notices printed, mailing scheduled' },
  { id: 'MN-WC020-214', state: 'MN', wire_center: 'Minneapolis-North', requirement: 'Section 214 application filed', requirement_type: 'section_214', status: 'overdue', due_date: '2026-08-15', completed_date: null, notes: 'OVERDUE — filing delayed by legal review backlog' },
  { id: 'MN-WC020-NOTICE', state: 'MN', wire_center: 'Minneapolis-North', requirement: '90-day residential notice mailed', requirement_type: 'residential_notice', status: 'blocked', due_date: '2026-09-01', completed_date: null, notes: 'Blocked on Section 214 filing' },
  { id: 'WA-WC030-214', state: 'WA', wire_center: 'Seattle-Eastside', requirement: 'Section 214 application filed', requirement_type: 'section_214', status: 'complete', due_date: '2026-08-01', completed_date: '2026-07-28', notes: 'Auto-granted 2026-08-28' },
  { id: 'WA-WC030-NOTICE', state: 'WA', wire_center: 'Seattle-Eastside', requirement: '90-day residential notice mailed', requirement_type: 'residential_notice', status: 'complete', due_date: '2026-08-15', completed_date: '2026-08-10', notes: '4,200 notices delivered' },
  { id: 'WA-WC030-911', state: 'WA', wire_center: 'Seattle-Eastside', requirement: 'PSAP coordination completed', requirement_type: '911_coordination', status: 'complete', due_date: '2026-08-01', completed_date: '2026-07-25', notes: 'King County PSAP confirmed' },
  { id: 'AZ-WC040-214', state: 'AZ', wire_center: 'Phoenix-Metro', requirement: 'Section 214 application filed', requirement_type: 'section_214', status: 'complete', due_date: '2026-09-01', completed_date: '2026-08-25', notes: 'Competitive area — streamlined approval' },
  { id: 'ID-WC050-214', state: 'ID', wire_center: 'Boise-Central', requirement: 'Section 214 application filed', requirement_type: 'section_214', status: 'complete', due_date: '2026-09-15', completed_date: '2026-09-05', notes: 'Auto-grant pending (31-day window)' },
];

// --- Mock documents ---

const MOCK_DOCUMENTS: RegDocument[] = [
  { doc_id: 'FCC-26-19', title: 'FCC 26-19: Accelerating Wireline Broadband Deployment', document_type: 'fcc_order', issuing_body: 'Federal Communications Commission', jurisdiction: 'Federal', effective_date: '2026-04-15', effective_end_date: null, keywords: ['section 214', 'copper retirement', '251(c)(5)', 'broadband deployment', 'tech-transition'], summary: 'Eliminates Section 251(c)(5) network-change filing. Streamlines Section 214(a) discontinuance with 31-day auto-grants. Adds 911 coordination. 90-day residential notice retained.' },
  { doc_id: '47CFR-63-71', title: '47 CFR §63.71 — Discontinuance Notice Requirements', document_type: 'legislative', issuing_body: 'Code of Federal Regulations', jurisdiction: 'Federal', effective_date: '2026-04-15', effective_end_date: null, keywords: ['notice requirements', 'discontinuance', 'residential subscribers'], summary: 'Specifies notice requirements for service discontinuance including 90-day direct notice to residential subscribers.' },
  { doc_id: 'CPUC-4CCR', title: 'CPUC Rule 4 CCR 723-2: Copper Retirement Procedures', document_type: 'puc_docket', issuing_body: 'Colorado Public Utilities Commission', jurisdiction: 'Colorado', effective_date: '2025-01-15', effective_end_date: null, keywords: ['broadband certification', 'rural continuity', 'lifeline', 'copper retirement', 'Colorado'], summary: 'Establishes Colorado-specific copper retirement procedures including broadband availability certification, rural service continuity planning, and Lifeline transition coordination.' },
  { doc_id: 'OR-PUC-AR650', title: 'Oregon PUC AR 650: Telecommunications Service Retirement', document_type: 'puc_docket', issuing_body: 'Oregon Public Utility Commission', jurisdiction: 'Oregon', effective_date: '2024-07-01', effective_end_date: null, keywords: ['120-day notice', 'service migration', 'rural exemption', 'Oregon'], summary: '120-day advance notice. Service migration plan required. Public comment period. Rural area extended 180-day notice.' },
  { doc_id: 'ACC-79XXX', title: 'ACC Decision No. 79XXX: Wireline Service Modifications', document_type: 'puc_docket', issuing_body: 'Arizona Corporation Commission', jurisdiction: 'Arizona', effective_date: '2023-11-20', effective_end_date: null, keywords: ['competitive areas', 'COLR', 'streamlined', 'Arizona'], summary: '60-day state notice (federal 90-day governs). Streamlined approval in competitive areas. COLR obligations preserved.' },
  { doc_id: 'USC-47-503', title: '47 U.S.C. §503(b): Forfeiture Penalties', document_type: 'legislative', issuing_body: 'United States Code', jurisdiction: 'Federal', effective_date: '2021-01-01', effective_end_date: null, keywords: ['penalties', 'enforcement', 'forfeiture', 'compliance'], summary: 'Establishes forfeiture penalties up to $100,000 per violation per day for non-compliance with Communications Act provisions.' },
  { doc_id: 'FCC-NOTICE-TEMPLATE', title: 'FCC Model Residential Notice Letter — Copper Retirement', document_type: 'notice_template', issuing_body: 'Federal Communications Commission', jurisdiction: 'Federal', effective_date: '2026-05-01', effective_end_date: null, keywords: ['notice template', 'residential', 'model letter'], summary: 'Model notice letter template for 90-day residential direct notice as required under FCC 26-19 and 47 CFR §63.71.' },
  { doc_id: 'FCC-911-GUIDE', title: 'FCC 911 Coordination Guide for Technology Transitions', document_type: 'guidance', issuing_body: 'Federal Communications Commission', jurisdiction: 'Federal', effective_date: '2026-06-01', effective_end_date: null, keywords: ['911', 'PSAP', 'emergency services', 'coordination'], summary: 'Step-by-step guide for carriers to coordinate with PSAPs and 911 authorities before retiring copper infrastructure.' },
];

// --- Mock KPIs ---

const MOCK_KPIS: RegKPIs = {
  jurisdictions_covered: 6,
  pending_filings: 6,
  days_until_next_deadline: 21,
  compliance_pct: 53.3,
  overdue_items: 1,
  documents_indexed: 8,
};

// --- Suggested questions for cold start ---

export const SUGGESTED_QUESTIONS = [
  'What is Section 214?',
  'Do we still need Section 214 authorization?',
  'What notice do we give residential customers?',
  'What changed with FCC 26-19?',
  "What are Colorado's requirements?",
  '911 coordination requirements?',
  'What are the penalties for non-compliance?',
  'How do we handle Lifeline subscribers?',
];

// --- Compliance status colors ---

export const COMPLIANCE_COLORS: Record<string, string> = {
  clear: '#22c55e',     // green
  pending: '#eab308',   // yellow
  blocked: '#ef4444',   // red
  overdue: '#dc2626',   // dark red
  flagged: '#f97316',   // orange
  complete: '#22c55e',  // green
};

export const REQUIREMENT_TYPE_LABELS: Record<string, string> = {
  section_214: 'Section 214',
  state_puc: 'State PUC Filing',
  residential_notice: 'Residential Notice',
  '911_coordination': '911 Coordination',
  environmental: 'Environmental Review',
};

// --- Getters ---

export function getMockQA(): AgentQA[] {
  return [...MOCK_QA];
}

export function findMockAnswer(question: string): AgentQA | null {
  const q = question.toLowerCase().trim();
  return MOCK_QA.find((qa) =>
    q.includes(qa.question.toLowerCase().slice(0, 20)) ||
    qa.question.toLowerCase().includes(q.slice(0, 20))
  ) ?? null;
}

export function getMockJurisdictions(stateFilter?: string): JurisdictionRow[] {
  if (stateFilter && stateFilter !== 'all') {
    return MOCK_JURISDICTIONS.filter((j) => j.state === stateFilter);
  }
  return [...MOCK_JURISDICTIONS];
}

export function getMockChecklist(filters?: {
  state?: string;
  status?: string;
  requirement_type?: string;
}): ChecklistItem[] {
  let items = [...MOCK_CHECKLIST];
  if (filters?.state && filters.state !== 'all') {
    items = items.filter((i) => i.state === filters.state);
  }
  if (filters?.status && filters.status !== 'all') {
    items = items.filter((i) => i.status === filters.status);
  }
  if (filters?.requirement_type && filters.requirement_type !== 'all') {
    items = items.filter((i) => i.requirement_type === filters.requirement_type);
  }
  return items;
}

export function getMockDocuments(filters?: {
  jurisdiction?: string;
  document_type?: string;
  search?: string;
}): RegDocument[] {
  let docs = [...MOCK_DOCUMENTS];
  if (filters?.jurisdiction && filters.jurisdiction !== 'all') {
    docs = docs.filter((d) => d.jurisdiction === filters.jurisdiction);
  }
  if (filters?.document_type && filters.document_type !== 'all') {
    docs = docs.filter((d) => d.document_type === filters.document_type);
  }
  if (filters?.search) {
    const s = filters.search.toLowerCase();
    docs = docs.filter((d) =>
      d.title.toLowerCase().includes(s) ||
      d.summary.toLowerCase().includes(s) ||
      d.keywords.some((k) => k.includes(s))
    );
  }
  return docs;
}

export function getMockKPIs(): RegKPIs {
  return { ...MOCK_KPIS };
}

export function getMockDocument(docId: string): RegDocument | null {
  return MOCK_DOCUMENTS.find((d) => d.doc_id === docId) ?? null;
}
