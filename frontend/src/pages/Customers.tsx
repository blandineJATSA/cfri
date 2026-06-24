import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { riskColor, riskLabel, formatCurrency } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Users, AlertTriangle } from 'lucide-react'

export default function CustomersPage() {
  const { data: customers, isLoading } = useQuery({
    queryKey: ['customers-risk'],
    queryFn: apiClient.getAtRiskCustomers,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-zinc-400 text-sm">Chargement...</p>
      </div>
    )
  }

  const highRisk = customers?.filter(
    c => c.risk_level === 'high' || c.risk_level === 'critical'
  ) ?? []

  const otherRisk = customers?.filter(
    c => c.risk_level === 'medium' || c.risk_level === 'low'
  ) ?? []

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-zinc-900">
          Clients à risque
        </h1>
        <p className="text-sm text-zinc-500 mt-1">
          Clients classés par probabilité de churn
        </p>
      </div>

      {/* Clients à risque élevé */}
      {highRisk.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="h-4 w-4 text-red-500" />
            <h2 className="text-sm font-semibold text-red-600">
              Action requise — {highRisk.length} client(s)
            </h2>
          </div>
          <div className="space-y-3">
            {highRisk.map((customer) => (
              <CustomerCard key={customer.customer_id} customer={customer} />
            ))}
          </div>
        </div>
      )}

      {/* Autres clients */}
      {otherRisk.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Users className="h-4 w-4 text-zinc-400" />
            <h2 className="text-sm font-semibold text-zinc-500">
              À surveiller — {otherRisk.length} client(s)
            </h2>
          </div>
          <div className="space-y-3">
            {otherRisk.map((customer) => (
              <CustomerCard key={customer.customer_id} customer={customer} />
            ))}
          </div>
        </div>
      )}

      {!customers || customers.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-zinc-400 text-sm">
              Aucun client scoré — importez des données et calculez le scoring
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function CustomerCard({ customer }: {
  customer: {
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
}) {
  return (
    <Card>
      <CardContent className="py-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            {/* Email et badge risque */}
            <div className="flex items-center gap-2 mb-2">
              <p className="text-sm font-medium text-zinc-900">
                {customer.email ?? 'Client inconnu'}
              </p>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${riskColor(customer.risk_level)}`}>
                {riskLabel(customer.risk_level)}
              </span>
            </div>

            {/* Stats */}
            <div className="flex items-center gap-4 mb-3">
              <p className="text-xs text-zinc-400">
                {formatCurrency(customer.total_spent)} dépensés
              </p>
              <p className="text-xs text-zinc-400">
                {customer.orders_count} commande(s)
              </p>
              <p className="text-xs font-medium text-zinc-600">
                Score : {customer.risk_score}/100
              </p>
            </div>

            {/* Raisons */}
            <div className="flex flex-wrap gap-1 mb-2">
              {customer.reasons.map((reason, i) => (
                <Badge key={i} variant="secondary" className="text-xs">
                  {reason}
                </Badge>
              ))}
            </div>

            {/* Action recommandée */}
            {customer.recommended_action && (
              <p className="text-xs text-zinc-500 mt-2">
                💡 {customer.recommended_action}
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}