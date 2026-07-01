import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient, PreviewResult, ColumnMapping } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Upload, FileText, Brain, TrendingUp,
  CheckCircle, AlertTriangle, Trash2, ChevronRight
} from 'lucide-react'

const FEEDBACK_FIELD_LABELS: Record<string, string> = {
  email: 'Email client *',
  body: 'Texte du feedback *',
  subject: 'Sujet',
  rating: 'Note',
  channel: 'Canal',
  feedback_date: 'Date',
}

const ORDER_FIELD_LABELS: Record<string, string> = {
  email: 'Email client *',
  total_amount: 'Montant total *',
  order_date: 'Date commande',
  refund_amount: 'Montant remboursé',
  status: 'Statut',
  product_name: 'Nom produit',
  order_id: 'ID commande',
}

function MappingEditor({
  preview,
  onConfirm,
  onCancel,
  importType,
}: {
  preview: PreviewResult
  onConfirm: (mapping: Record<string, string | null>) => void
  onCancel: () => void
  importType: 'feedbacks' | 'orders'
}) {
  const fieldLabels = importType === 'feedbacks' ? FEEDBACK_FIELD_LABELS : ORDER_FIELD_LABELS
  const [mapping, setMapping] = useState<Record<string, string | null>>(
    preview.mapping as unknown as Record<string, string | null>
  )

  const missingRequired = Object.entries(fieldLabels)
    .filter(([key, label]) => label.includes('*') && !mapping[key])
    .map(([key]) => key)

  return (
    <div className="space-y-4">
      <div className="rounded-lg bg-zinc-50 border border-zinc-200 p-4">
        <p className="text-xs font-medium text-zinc-500 mb-2">
          Colonnes détectées dans votre fichier
        </p>
        <div className="flex flex-wrap gap-2">
          {preview.columns.map(col => (
            <Badge key={col} variant="outline" className="text-xs">
              {col}
            </Badge>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-xs font-medium text-zinc-700">
          Associez vos colonnes aux champs CFRI
        </p>
        {Object.entries(fieldLabels).map(([cfriField, label]) => (
          <div key={cfriField} className="flex items-center gap-3">
            <div className="w-40 shrink-0">
              <p className="text-xs text-zinc-600">{label}</p>
            </div>
            <ChevronRight className="h-3 w-3 text-zinc-300 shrink-0" />
            <select
              value={mapping[cfriField] ?? ''}
              onChange={(e) =>
                setMapping(prev => ({
                  ...prev,
                  [cfriField]: e.target.value || null,
                }))
              }
              className="flex-1 text-xs border border-zinc-200 rounded-md px-2 py-1.5 bg-white text-zinc-700 focus:outline-none focus:ring-1 focus:ring-zinc-400"
            >
              <option value="">— Non mappé —</option>
              {preview.columns.map(col => (
                <option key={col} value={col}>{col}</option>
              ))}
            </select>
            {mapping[cfriField] && (
              <CheckCircle className="h-3.5 w-3.5 text-green-500 shrink-0" />
            )}
          </div>
        ))}
      </div>

      {preview.preview_rows.length > 0 && (
        <div className="rounded-lg border border-zinc-200 overflow-hidden">
          <p className="text-xs font-medium text-zinc-500 px-3 py-2 bg-zinc-50 border-b border-zinc-200">
            Aperçu des 3 premières lignes
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-zinc-100">
                  {Object.keys(fieldLabels).filter(f => mapping[f]).map(field => (
                    <th key={field} className="px-3 py-2 text-left text-zinc-500 font-medium">
                      {fieldLabels[field].replace(' *', '')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.preview_rows.map((row, i) => (
                  <tr key={i} className="border-b border-zinc-50 last:border-0">
                    {Object.keys(fieldLabels).filter(f => mapping[f]).map(field => (
                      <td key={field} className="px-3 py-2 text-zinc-600 max-w-32 truncate">
                        {String(row[mapping[field]!] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {missingRequired.length > 0 && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 flex items-start gap-2">
          <AlertTriangle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
          <p className="text-xs text-red-700">
            Champs obligatoires non mappés : {missingRequired.join(', ')}. Vous devez les associer pour continuer.
          </p>
        </div>
      )}

      <div className="flex gap-2 pt-2">
        <Button size="sm" variant="outline" onClick={onCancel} className="flex-1">
          Annuler
        </Button>
        <Button
          size="sm"
          onClick={() => onConfirm(mapping)}
          disabled={missingRequired.length > 0}
          className="flex-1"
        >
          Confirmer et importer
        </Button>
      </div>
    </div>
  )
}

export default function ImportPage() {
  const [feedbackFile, setFeedbackFile] = useState<File | null>(null)
  const [orderFile, setOrderFile] = useState<File | null>(null)
  const [feedbackPreview, setFeedbackPreview] = useState<PreviewResult | null>(null)
  const [orderPreview, setOrderPreview] = useState<PreviewResult | null>(null)
  const [log, setLog] = useState<string[]>([])
  const [step, setStep] = useState<'idle' | 'analyzed' | 'scored'>('idle')

  const addLog = (msg: string) => setLog(prev => [...prev, msg])

  const previewFeedbacksMutation = useMutation({
    mutationFn: () => apiClient.previewFeedbacks(feedbackFile!),
    onSuccess: (data) => {
      setFeedbackPreview(data)
      if (data.missing_required.length > 0) {
        addLog(`⚠️ Colonnes obligatoires non détectées : ${data.missing_required.join(', ')} — vérifiez le mapping`)
      } else {
        addLog(`✅ Fichier analysé — ${data.columns.length} colonnes détectées`)
      }
    },
    onError: () => addLog('❌ Impossible de lire le fichier CSV'),
  })

  const previewOrdersMutation = useMutation({
    mutationFn: () => apiClient.previewOrders(orderFile!),
    onSuccess: (data) => {
      setOrderPreview(data)
      if (data.missing_required.length > 0) {
        addLog(`⚠️ Colonnes obligatoires non détectées : ${data.missing_required.join(', ')} — vérifiez le mapping`)
      } else {
        addLog(`✅ Fichier commandes analysé — ${data.columns.length} colonnes détectées`)
      }
    },
    onError: () => addLog('❌ Impossible de lire le fichier CSV'),
  })

  const uploadFeedbacksMutation = useMutation({
    mutationFn: (mapping: Record<string, string | null>) =>
      apiClient.uploadFeedbacksWithMapping(feedbackFile!, mapping as unknown as ColumnMapping),
    onSuccess: (data) => {
      addLog(`✅ ${data.rows_processed} feedbacks importés`)
      if (data.error_message?.includes('doublons')) {
        addLog(`ℹ️ ${data.error_message}`)
      }
      setFeedbackPreview(null)
      setFeedbackFile(null)
      refetchImports()
    },
    onError: () => addLog('❌ Erreur lors de l\'import des feedbacks'),
  })

  const uploadOrdersMutation = useMutation({
    mutationFn: () => apiClient.uploadOrders(orderFile!),
    onSuccess: (data) => {
      addLog(`✅ ${data.rows_processed} commandes importées`)
      if (data.error_message?.includes('doublons')) {
        addLog(`ℹ️ ${data.error_message}`)
      }
      setOrderPreview(null)
      setOrderFile(null)
      refetchImports()
    },
    onError: () => addLog('❌ Erreur lors de l\'import des commandes'),
  })

  const analysisMutation = useMutation({
    mutationFn: apiClient.runAnalysis,
    onSuccess: async (data) => {
      if (data.status === 'nothing_to_analyze') {
        addLog('✅ Tous les feedbacks sont déjà analysés')
        setStep('analyzed')
        return
      }
      if (data.status === 'completed') {
        addLog(`✅ ${data.success} feedbacks analysés`)
        if (data.total > 0 && data.success > 0) {
          setTimeout(() => analysisMutation.mutate(), 3000)
        } else {
          setStep('analyzed')
        }
        return
      }
      addLog('🔄 Analyse en arrière-plan...')
      const jobId = data.job_id
      if (jobId) {
        const pollStatus = async () => {
          const status = await apiClient.getJobStatus(jobId)
          if (status.status === 'finished') {
            addLog(`✅ ${status.result?.success ?? 20} feedbacks analysés`)
            setTimeout(() => analysisMutation.mutate(), 2000)
          } else if (status.status === 'failed') {
            addLog('❌ Erreur — nouvelle tentative dans 5s...')
            setTimeout(() => analysisMutation.mutate(), 5000)
          } else {
            setTimeout(pollStatus, 3000)
          }
        }
        setTimeout(pollStatus, 3000)
      }
    },
    onError: () => {
      addLog('❌ Erreur — nouvelle tentative dans 5s...')
      setTimeout(() => analysisMutation.mutate(), 5000)
    },
  })

  const scoringMutation = useMutation({
    mutationFn: apiClient.computeScoring,
    onSuccess: (data) => {
      addLog(`✅ ${data.problems_computed} problèmes calculés`)
      addLog(`✅ ${data.risk_scores_computed} clients scorés`)
      setStep('scored')
    },
    onError: () => addLog('❌ Erreur lors du calcul du scoring'),
  })

  const { data: imports, refetch: refetchImports } = useQuery({
    queryKey: ['imports'],
    queryFn: apiClient.getImports,
  })

  const deleteImportMutation = useMutation({
    mutationFn: apiClient.deleteImport,
    onSuccess: () => {
      addLog('🗑️ Import supprimé')
      refetchImports()
    },
  })

  const { data: analysisStatus } = useQuery({
    queryKey: ['analysis-status'],
    queryFn: apiClient.getAnalysisStatus,
    refetchInterval: analysisMutation.isPending ? 3000 : false,
  })

  const isLoading =
    uploadFeedbacksMutation.isPending ||
    uploadOrdersMutation.isPending ||
    previewFeedbacksMutation.isPending ||
    previewOrdersMutation.isPending ||
    scoringMutation.isPending

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-zinc-900">Importer des données</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Uploadez vos fichiers CSV pour analyser vos feedbacks clients
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">

          {/* Upload feedbacks */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Fichier feedbacks (obligatoire)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {!feedbackPreview ? (
                <>
                  <p className="text-xs text-zinc-400">
                    Colonnes attendues : email, body, subject, rating, channel, feedback_date
                  </p>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => {
                      setFeedbackFile(e.target.files?.[0] ?? null)
                      setFeedbackPreview(null)
                    }}
                    className="text-sm text-zinc-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-medium file:bg-zinc-100 file:text-zinc-700 hover:file:bg-zinc-200 cursor-pointer"
                  />
                  {feedbackFile && (
                    <p className="text-xs text-zinc-500">📄 {feedbackFile.name}</p>
                  )}
                  <Button
                    onClick={() => {
                      addLog('🔍 Analyse du fichier...')
                      previewFeedbacksMutation.mutate()
                    }}
                    disabled={!feedbackFile || isLoading}
                    size="sm"
                    className="w-full"
                  >
                    <Upload className="h-3.5 w-3.5 mr-2" />
                    Analyser le fichier
                  </Button>
                </>
              ) : (
                <MappingEditor
                  preview={feedbackPreview}
                  importType="feedbacks"
                  onConfirm={(mapping) => {
                    addLog('📤 Import feedbacks en cours...')
                    uploadFeedbacksMutation.mutate(mapping)
                  }}
                  onCancel={() => setFeedbackPreview(null)}
                />
              )}
            </CardContent>
          </Card>

          {/* Upload commandes */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Fichier commandes (optionnel)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {!orderPreview ? (
                <>
                  <p className="text-xs text-zinc-400">
                    Colonnes attendues : email, total_amount, order_date, refund_amount, status, product_name
                  </p>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => {
                      setOrderFile(e.target.files?.[0] ?? null)
                      setOrderPreview(null)
                    }}
                    className="text-sm text-zinc-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-medium file:bg-zinc-100 file:text-zinc-700 hover:file:bg-zinc-200 cursor-pointer"
                  />
                  {orderFile && (
                    <p className="text-xs text-zinc-500">📄 {orderFile.name}</p>
                  )}
                  <Button
                    onClick={() => {
                      addLog('🔍 Analyse du fichier commandes...')
                      previewOrdersMutation.mutate()
                    }}
                    disabled={!orderFile || isLoading}
                    size="sm"
                    variant="outline"
                    className="w-full"
                  >
                    <Upload className="h-3.5 w-3.5 mr-2" />
                    Analyser le fichier
                  </Button>
                </>
              ) : (
                <MappingEditor
                  preview={orderPreview}
                  importType="orders"
                  onConfirm={(_mapping) => {
                    addLog('📤 Import commandes en cours...')
                    uploadOrdersMutation.mutate()
                  }}
                  onCancel={() => setOrderPreview(null)}
                />
              )}
            </CardContent>
          </Card>

          {/* Étapes suivantes */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Étapes suivantes</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Brain className="h-4 w-4 text-zinc-400" />
                  <div>
                    <p className="text-sm font-medium">Analyse IA</p>
                    {analysisStatus && (
                      <p className="text-xs text-zinc-400">
                        {analysisStatus.analyzed}/{analysisStatus.total_feedbacks} analysés
                      </p>
                    )}
                  </div>
                </div>
                <Button
                  onClick={() => {
                    addLog('🤖 Analyse IA en cours...')
                    analysisMutation.mutate()
                  }}
                  disabled={isLoading}
                  size="sm"
                  variant="outline"
                >
                  Lancer
                </Button>
              </div>

              <div className="border-t border-zinc-100" />

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-zinc-400" />
                  <div>
                    <p className="text-sm font-medium">Calcul scoring</p>
                    <p className="text-xs text-zinc-400">Impact revenue + risk score</p>
                  </div>
                </div>
                <Button
                  onClick={() => {
                    addLog('📊 Calcul scoring en cours...')
                    scoringMutation.mutate()
                  }}
                  disabled={isLoading}
                  size="sm"
                  variant="outline"
                >
                  Calculer
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Colonne droite */}
        <div className="space-y-4">

          {/* Journal d'activité */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <CheckCircle className="h-4 w-4" />
                Journal d'activité
              </CardTitle>
            </CardHeader>
            <CardContent>
              {log.length === 0 ? (
                <p className="text-xs text-zinc-400 text-center py-8">
                  Les actions apparaîtront ici...
                </p>
              ) : (
                <div className="space-y-2">
                  {log.map((entry, i) => (
                    <p key={i} className="text-xs text-zinc-600 font-mono">{entry}</p>
                  ))}
                  {step === 'scored' && (
                    <div className="mt-4 p-3 bg-green-50 rounded-md">
                      <p className="text-xs font-medium text-green-700">
                        ✅ Tout est prêt — consultez le dashboard !
                      </p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Historique des imports */}
          {imports && imports.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">
                  Historique des imports
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {imports.map((imp) => (
                  <div
                    key={imp.id}
                    className="flex items-center justify-between py-2 border-b border-zinc-100 last:border-0"
                  >
                    <div>
                      <p className="text-xs font-medium text-zinc-700">
                        {imp.filename}
                      </p>
                      <p className="text-xs text-zinc-400">
                        {imp.rows_processed} lignes ·{' '}
                        {new Date(imp.created_at).toLocaleDateString('fr-FR')}
                        {imp.error_message && (
                          <span className="text-amber-500 ml-1">· {imp.error_message}</span>
                        )}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className={`text-xs ${
                          imp.status === 'completed'
                            ? 'text-green-600 border-green-200'
                            : imp.status === 'failed'
                            ? 'text-red-600 border-red-200'
                            : 'text-zinc-500'
                        }`}
                      >
                        {imp.status}
                      </Badge>
                      <button
                        onClick={() => {
                          if (confirm('Supprimer cet import et toutes ses données ?')) {
                            deleteImportMutation.mutate(imp.id)
                          }
                        }}
                        className="text-zinc-300 hover:text-red-500 transition-colors"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}