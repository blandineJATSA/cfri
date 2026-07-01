import { useQuery, useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '@/lib/api'
import { formatCurrency, formatNumber } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  MessageSquare, Users, TrendingUp,
  AlertTriangle, RefreshCw, Euro, Upload, Sparkles
} from 'lucide-react'

export default function DashboardPage() {
  const navigate = useNavigate()

  const { data: summary, refetch: refetchSummary } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: apiClient.getDashboardSummary,
  })

  const { data: problems } = useQuery({
    queryKey: ['problems'],
    queryFn: apiClient.getProblems,
  })

  const computeMutation = useMutation({
    mutationFn: apiClient.computeScoring,
    onSuccess: () => refetchSummary(),
  })

  const isDemo = summary?.is_demo === true

  return (
    <div>
      {/* Banner demo */}
      {isDemo && (
        <div className="mb-6 rounded-lg bg-amber-50 border border-amber-200 px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Sparkles className="h-5 w-5 text-amber-500 shrink-0" />
            <div>
              <p className="text-sm font-medium text-amber-800">
                Vous regardez des données de démonstration
              </p>
              <p className="text-xs text-amber-600 mt-0.5">
                Importez vos propres feedbacks pour voir l'analyse de votre activité réelle
              </p>
            </div>
          </div>
          <Button
            size="sm"
            onClick={() => navigate('/import')}
            className="bg-amber-500 hover:bg-amber-600 text-white shrink-0 gap-2"
          >
            <Upload className="h-3.5 w-3.5" />
            Importer mes données
          </Button>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-900">
            Vue d'ensemble
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            {isDemo ? 'Données de démonstration — marque de mode fictive' : 'Analyse de vos feedbacks clients'}
          </p>
        </div>
        {!isDemo && (
          <Button
            onClick={() => computeMutation.mutate()}
            disabled={computeMutation.isPending}
            variant="outline"
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${computeMutation.isPending ? 'animate-spin' : ''}`} />
            Recalculer
          </Button>
        )}
      </div>

      {/* Métriques clés */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4 mb-8">
        <Card className={isDemo ? 'border-amber-200' : ''}>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-zinc-500 flex items-center gap-2">
              <MessageSquare className="h-3.5 w-3.5" />
              Feedbacks analysés
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">
              {formatNumber(summary?.analyzed_count ?? 0)}
            </p>
            <p className="text-xs text-zinc-400 mt-1">
              sur {formatNumber(summary?.feedbacks_count ?? 0)} total
            </p>
          </CardContent>
        </Card>

        <Card className={isDemo ? 'border-amber-200' : ''}>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-zinc-500 flex items-center gap-2">
              <Users className="h-3.5 w-3.5" />
              Clients
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">
              {formatNumber(summary?.customers_count ?? 0)}
            </p>
            <p className="text-xs text-red-500 mt-1">
              {summary?.at_risk_customers ?? 0} à risque élevé
            </p>
          </CardContent>
        </Card>

        <Card className={isDemo ? 'border-amber-200' : ''}>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-zinc-500 flex items-center gap-2">
              <Euro className="h-3.5 w-3.5" />
              CA associé aux problèmes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">
              {formatCurrency(summary?.total_revenue ?? 0)}
            </p>
            <p className="text-xs text-zinc-400 mt-1">
              {formatCurrency(summary?.total_refunds ?? 0)} remboursés
            </p>
          </CardContent>
        </Card>

        <Card className={isDemo ? 'border-amber-200' : ''}>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-zinc-500 flex items-center gap-2">
              <AlertTriangle className="h-3.5 w-3.5" />
              Problèmes détectés
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">
              {summary?.problems_count ?? 0}
            </p>
            <p className="text-xs text-zinc-400 mt-1">
              catégories distinctes
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Top problèmes */}
      <Card className={isDemo ? 'border-amber-200' : ''}>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Top problèmes par impact
            {isDemo && (
              <Badge className="bg-amber-100 text-amber-700 border-amber-200 text-xs ml-2">
                Démo
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!problems || problems.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-sm text-zinc-400 mb-3">
                Aucun problème détecté — importez des feedbacks et lancez l'analyse
              </p>
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigate('/import')}
                className="gap-2"
              >
                <Upload className="h-3.5 w-3.5" />
                Importer mes données
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {problems.slice(0, 5).map((problem, i) => (
                <div
                  key={problem.id}
                  className="flex items-center justify-between py-2 border-b border-zinc-100 last:border-0"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-zinc-400 w-5">
                      {i + 1}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-zinc-900">
                        {problem.title}
                      </p>
                      <p className="text-xs text-zinc-400">
                        {problem.feedback_count} feedbacks ·{' '}
                        {problem.customers_count} clients ·{' '}
                        {problem.negative_rate}% négatifs
                      </p>
                    </div>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    Score {problem.impact_score}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* CTA onboarding bas de page */}
      {isDemo && (
        <div className="mt-6 rounded-lg bg-zinc-900 px-6 py-5 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-white">
              Prêt à analyser vos vrais feedbacks ?
            </p>
            <p className="text-xs text-zinc-400 mt-0.5">
              Importez vos tickets support et commandes en moins de 2 minutes
            </p>
          </div>
          <Button
            size="sm"
            onClick={() => navigate('/import')}
            className="bg-white text-zinc-900 hover:bg-zinc-100 shrink-0 gap-2"
          >
            <Upload className="h-3.5 w-3.5" />
            Commencer
          </Button>
        </div>
      )}
    </div>
  )
}