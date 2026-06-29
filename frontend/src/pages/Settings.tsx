import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, CreditCard, Settings } from 'lucide-react'

interface Plan {
  id: string
  name: string
  price: number
  currency: string
  price_id: string
  features: string[]
}

interface BillingStatus {
  plan: string
  organization_id: string
}

export default function SettingsPage() {
  const { data: plans } = useQuery({
    queryKey: ['billing-plans'],
    queryFn: () => api.get<Plan[]>('/billing/plans').then(r => r.data),
  })

  const { data: status } = useQuery({
    queryKey: ['billing-status'],
    queryFn: () => api.get<BillingStatus>('/billing/status').then(r => r.data),
  })

  const checkoutMutation = useMutation({
    mutationFn: (price_id: string) =>
      api.post('/billing/checkout', { price_id }).then(r => r.data),
    onSuccess: (data) => {
      // Rediriger vers la page de paiement Stripe
      window.location.href = data.url
    },
    onError: (err: any) => {
      alert('Erreur : ' + (err.response?.data?.detail ?? err.message))
    },
  })

  const portalMutation = useMutation({
    mutationFn: () =>
      api.post('/billing/portal').then(r => r.data),
    onSuccess: (data) => {
      window.location.href = data.url
    },
  })

  const planLabel: Record<string, string> = {
    free: 'Gratuit',
    starter: 'Starter',
    growth: 'Growth',
    business: 'Business',
  }

  const planColor: Record<string, string> = {
    free: 'bg-zinc-100 text-zinc-600',
    starter: 'bg-blue-50 text-blue-700',
    growth: 'bg-purple-50 text-purple-700',
    business: 'bg-amber-50 text-amber-700',
  }

  const currentPlan = status?.plan ?? 'free'

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-zinc-900 flex items-center gap-2">
          <Settings className="h-6 w-6" />
          Paramètres
        </h1>
        <p className="text-sm text-zinc-500 mt-1">
          Gérez votre abonnement et votre facturation
        </p>
      </div>

      {/* Plan actuel */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <CreditCard className="h-4 w-4" />
            Plan actuel
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className={`text-sm font-medium px-3 py-1 rounded-full ${planColor[currentPlan]}`}>
                {planLabel[currentPlan] ?? currentPlan}
              </span>
              {currentPlan !== 'free' && (
                <p className="text-sm text-zinc-500">
                  Abonnement actif
                </p>
              )}
              {currentPlan === 'free' && (
                <p className="text-sm text-zinc-500">
                  Passez à un plan payant pour débloquer toutes les fonctionnalités
                </p>
              )}
            </div>
            {currentPlan !== 'free' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => portalMutation.mutate()}
                disabled={portalMutation.isPending}
              >
                Gérer l'abonnement
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Plans disponibles */}
      <h2 className="text-lg font-semibold text-zinc-900 mb-4">
        Choisir un plan
      </h2>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {plans?.map((plan) => (
          <Card
            key={plan.id}
            className={`relative ${currentPlan === plan.id ? 'ring-2 ring-zinc-900' : ''}`}
          >
            {currentPlan === plan.id && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <Badge className="bg-zinc-900 text-white text-xs">
                  Plan actuel
                </Badge>
              </div>
            )}
            <CardHeader>
              <CardTitle className="text-base font-semibold">
                {plan.name}
              </CardTitle>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-bold text-zinc-900">
                  {plan.price}€
                </span>
                <span className="text-sm text-zinc-400">/mois</span>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="space-y-2">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-zinc-600">
                    <CheckCircle className="h-3.5 w-3.5 text-green-500 shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>
              <Button
                className="w-full"
                variant={currentPlan === plan.id ? 'outline' : 'default'}
                disabled={
                  currentPlan === plan.id ||
                  checkoutMutation.isPending
                }
                onClick={() => checkoutMutation.mutate(plan.price_id)}
              >
                {currentPlan === plan.id
                  ? 'Plan actuel'
                  : checkoutMutation.isPending
                  ? 'Chargement...'
                  : `Choisir ${plan.name}`}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}