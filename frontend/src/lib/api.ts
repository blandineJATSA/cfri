import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

/**
 * Intercepteur de requête — récupère un token Clerk frais avant chaque appel.
 * Le token Clerk dure 60 secondes mais se renouvelle automatiquement.
 * On le récupère à chaque requête pour être sûr d'avoir toujours un token valide.
 */
api.interceptors.request.use(async (config) => {
  try {
    const token = await (window as any).Clerk?.session?.getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
  } catch (e) {
    // Clerk pas encore chargé — on continue sans token
  }
  return config
})

// ── Types ──────────────────────────────────────────────

export interface DashboardSummary {
  feedbacks_count: number
  analyzed_count: number
  customers_count: number
  total_revenue: number
  total_refunds: number
  problems_count: number
  at_risk_customers: number
}

export interface Problem {
  id: string
  category: string
  subcategory: string | null
  title: string
  feedback_count: number
  customers_count: number
  associated_revenue: number
  refund_amount: number
  negative_rate: number
  impact_score: number
}

export interface CustomerRisk {
  customer_id: string
  email: string | null
  name: string | null
  total_spent: number
  orders_count: number
  risk_score: number
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  reasons: string[]
  recommended_action: string | null
}

export interface ImportRecord {
  id: string
  type: string
  filename: string
  status: string
  rows_total: number
  rows_processed: number
  error_message: string | null
  created_at: string
  completed_at: string | null
}

// ── Fonctions API ──────────────────────────────────────

export const apiClient = {
  getDashboardSummary: () =>
    api.get<DashboardSummary>('/dashboard/summary').then(r => r.data),

  computeScoring: () =>
    api.post('/dashboard/compute').then(r => r.data),

  getProblems: () =>
    api.get<Problem[]>('/problems').then(r => r.data),

  getAtRiskCustomers: () =>
    api.get<CustomerRisk[]>('/customers/risk').then(r => r.data),

  uploadFeedbacks: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<ImportRecord>('/imports/feedbacks', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },

  uploadOrders: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<ImportRecord>('/imports/orders', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },

  runAnalysis: () =>
    api.post('/analysis/run').then(r => r.data),

  getAnalysisStatus: () =>
    api.get('/analysis/status').then(r => r.data),

  getJobStatus: (jobId: string) =>
    api.get(`/analysis/job/${jobId}`).then(r => r.data),
}