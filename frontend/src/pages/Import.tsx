import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Upload, FileText, Brain, TrendingUp, CheckCircle } from 'lucide-react'

export default function ImportPage() {
  const [feedbackFile, setFeedbackFile] = useState<File | null>(null)
  const [orderFile, setOrderFile] = useState<File | null>(null)
  const [step, setStep] = useState<'idle' | 'imported' | 'analyzed' | 'scored'>('imported')
  const [log, setLog] = useState<string[]>([])

  const addLog = (msg: string) => setLog(prev => [...prev, msg])

  // Upload feedbacks
  const uploadFeedbacksMutation = useMutation({
    mutationFn: () => apiClient.uploadFeedbacks(feedbackFile!),
    onSuccess: (data) => {
      addLog(`✅ ${data.rows_processed} feedbacks importés`)
      setStep('imported')
    },
    onError: () => addLog('❌ Erreur lors de l\'import des feedbacks'),
  })

  // Upload commandes
  const uploadOrdersMutation = useMutation({
    mutationFn: () => apiClient.uploadOrders(orderFile!),
    onSuccess: (data) => {
      addLog(`✅ ${data.rows_processed} commandes importées`)
    },
    onError: () => addLog('❌ Erreur lors de l\'import des commandes'),
  })

  // Analyse IA
  const analysisMutation = useMutation({
  mutationFn: apiClient.runAnalysis,
  onSuccess: async (data) => {
    if (data.status === 'nothing_to_analyze') {
      addLog('✅ Tous les feedbacks sont déjà analysés')
      setStep('analyzed')
      return
    }

    if (data.status === 'completed') {
      // Fallback sans Redis
      addLog(`✅ ${data.success} feedbacks analysés`)
      if (data.total > 0 && data.success > 0) {
        setTimeout(() => analysisMutation.mutate(), 3000)
      } else {
        setStep('analyzed')
      }
      return
    }

    // Job Redis créé — on poll le statut
    addLog(`🔄 Job créé — analyse en arrière-plan...`)
    const jobId = data.job_id

    if (jobId) {
      const pollStatus = async () => {
        const status = await apiClient.getJobStatus(jobId)

        if (status.status === 'finished') {
          const result = status.result
          addLog(`✅ ${result?.success ?? 20} feedbacks analysés par l'IA`)
          // Relancer pour le batch suivant
          setTimeout(() => analysisMutation.mutate(), 2000)
        } else if (status.status === 'failed') {
          addLog('❌ Erreur — nouvelle tentative dans 5s...')
          setTimeout(() => analysisMutation.mutate(), 5000)
        } else {
          // En cours — on recheck dans 3 secondes
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

  // Scoring
  const scoringMutation = useMutation({
    mutationFn: apiClient.computeScoring,
    onSuccess: (data) => {
      addLog(`✅ ${data.problems_computed} problèmes calculés`)
      addLog(`✅ ${data.risk_scores_computed} clients scorés`)
      setStep('scored')
    },
    onError: () => addLog('❌ Erreur lors du calcul du scoring'),
  })

  const { data: analysisStatus } = useQuery({
    queryKey: ['analysis-status'],
    queryFn: apiClient.getAnalysisStatus,
    refetchInterval: step === 'imported' ? 3000 : false,
  })


  const isLoading = 
    uploadFeedbacksMutation.isPending ||
    uploadOrdersMutation.isPending ||
    scoringMutation.isPending

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-zinc-900">
          Importer des données
        </h1>
        <p className="text-sm text-zinc-500 mt-1">
          Uploadez vos fichiers CSV pour analyser vos feedbacks clients
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Colonne gauche — Upload */}
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
              <p className="text-xs text-zinc-400">
                Colonnes attendues : email, body, subject, rating, channel, feedback_date
              </p>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setFeedbackFile(e.target.files?.[0] ?? null)}
                className="text-sm text-zinc-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-medium file:bg-zinc-100 file:text-zinc-700 hover:file:bg-zinc-200 cursor-pointer"
              />
              {feedbackFile && (
                <p className="text-xs text-zinc-500">
                  📄 {feedbackFile.name}
                </p>
              )}
              <Button
                onClick={() => {
                  addLog('📤 Import feedbacks en cours...')
                  uploadFeedbacksMutation.mutate()
                }}
                disabled={!feedbackFile || isLoading}
                size="sm"
                className="w-full"
              >
                <Upload className="h-3.5 w-3.5 mr-2" />
                Importer les feedbacks
              </Button>
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
              <p className="text-xs text-zinc-400">
                Colonnes attendues : email, total_amount, order_date, refund_amount, status, product_name
              </p>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setOrderFile(e.target.files?.[0] ?? null)}
                className="text-sm text-zinc-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-medium file:bg-zinc-100 file:text-zinc-700 hover:file:bg-zinc-200 cursor-pointer"
              />
              {orderFile && (
                <p className="text-xs text-zinc-500">
                  📄 {orderFile.name}
                </p>
              )}
              <Button
                onClick={() => {
                  addLog('📤 Import commandes en cours...')
                  uploadOrdersMutation.mutate()
                }}
                disabled={!orderFile || isLoading}
                size="sm"
                variant="outline"
                className="w-full"
              >
                <Upload className="h-3.5 w-3.5 mr-2" />
                Importer les commandes
              </Button>
            </CardContent>
          </Card>

          {/* Étapes suivantes */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Étapes suivantes
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {/* Analyse IA */}
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

              {/* Scoring */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-zinc-400" />
                  <div>
                    <p className="text-sm font-medium">Calcul scoring</p>
                    <p className="text-xs text-zinc-400">
                      Impact revenue + risk score
                    </p>
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

        {/* Colonne droite — Log */}
        <div>
          <Card className="h-full">
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
                    <p key={i} className="text-xs text-zinc-600 font-mono">
                      {entry}
                    </p>
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
        </div>
      </div>
    </div>
  )
}