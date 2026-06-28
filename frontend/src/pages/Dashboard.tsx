import { useQuery, useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { formatCurrency, formatNumber } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  MessageSquare, Users, TrendingUp,
  AlertTriangle, RefreshCw, Euro
} from 'lucide-react'

export default function DashboardPage() {
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
    onSuccess: () => {
      refetchSummary()
    },
  })

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-900">
            Vue d'ensemble
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            Analyse de vos feedbacks clients
          </p>
        </div>
        <Button
          onClick={() => computeMutation.mutate()}
          disabled={computeMutation.isPending}
          variant="outline"
          className="gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${computeMutation.isPending ? 'animate-spin' : ''}`} />
          Recalculer
        </Button>
      </div>

      {/* Métriques clés */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4 mb-8">
        <Card>
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

        <Card>
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

        <Card>
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

        <Card>
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
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Top problèmes par impact
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!problems || problems.length === 0 ? (
            <p className="text-sm text-zinc-400 py-4 text-center">
              Aucun problème détecté — importez des feedbacks et lancez l'analyse
            </p>
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
                  <div className="text-right">
                    <Badge variant="outline" className="text-xs">
                      Score {problem.impact_score}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}