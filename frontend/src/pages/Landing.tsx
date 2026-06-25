import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import {
  TrendingUp, AlertTriangle, Users,
  ArrowRight, Upload, Brain, BarChart3,
  CheckCircle
} from 'lucide-react'

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-white">

      {/* Header */}
      <header className="flex items-center justify-between px-8 py-5 border-b border-zinc-100">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-zinc-900">
            <TrendingUp className="h-4 w-4 text-white" />
          </div>
          <span className="font-semibold text-zinc-900">CFRI</span>
        </div>
        <Button
          onClick={() => navigate('/dashboard')}
          size="sm"
        >
          Voir la démo
          <ArrowRight className="h-4 w-4" />
        </Button>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-4xl px-8 py-24 text-center">
        <div className="inline-flex items-center gap-2 rounded-full bg-zinc-100 px-4 py-1.5 text-xs font-medium text-zinc-600 mb-8">
          ✦ Analyse IA de feedbacks clients
        </div>
        <h1 className="text-5xl font-bold text-zinc-900 leading-tight mb-6">
          Découvrez quels problèmes clients
          <span className="text-zinc-400"> vous coûtent le plus cher</span>
        </h1>
        <p className="text-xl text-zinc-500 max-w-2xl mx-auto mb-10">
          Importez vos tickets support et commandes. En quelques minutes,
          CFRI identifie vos problèmes prioritaires et leur impact en euros.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Button
            onClick={() => navigate('/dashboard')}
            size="lg"
            className="gap-2 px-8"
          >
            Voir la démo
            <ArrowRight className="h-4 w-4" />
          </Button>
          <Button
            onClick={() => navigate('/import')}
            variant="outline"
            size="lg"
            className="gap-2"
          >
            <Upload className="h-4 w-4" />
            Importer mes données
          </Button>
        </div>
      </section>

      {/* Problèmes résolus */}
      <section className="bg-zinc-50 py-20">
        <div className="mx-auto max-w-4xl px-8">
          <h2 className="text-2xl font-semibold text-zinc-900 text-center mb-4">
            Le problème que tout e-commerçant connaît
          </h2>
          <p className="text-zinc-500 text-center mb-12 max-w-2xl mx-auto">
            Vos données clients sont partout — Zendesk, Shopify, Gmail, Trustpilot.
            Personne ne voit le tableau complet.
          </p>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <ProblemCard
              icon={<AlertTriangle className="h-5 w-5 text-orange-500" />}
              title="800 tickets par mois"
              description="Vous savez que vous avez des problèmes. Mais lesquels coûtent vraiment le plus cher ?"
            />
            <ProblemCard
              icon={<Users className="h-5 w-5 text-red-500" />}
              title="Clients qui partent"
              description="Certains clients mécontents ne rachètent jamais. Vous ne savez pas lesquels contacter en priorité."
            />
            <ProblemCard
              icon={<TrendingUp className="h-5 w-5 text-zinc-400" />}
              title="Données dispersées"
              description="Le support voit les plaintes. La finance voit les remboursements. Personne ne fait le lien."
            />
          </div>
        </div>
      </section>

      {/* Comment ça marche */}
      <section className="py-20">
        <div className="mx-auto max-w-4xl px-8">
          <h2 className="text-2xl font-semibold text-zinc-900 text-center mb-12">
            Comment ça marche
          </h2>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            <StepCard
              number="1"
              icon={<Upload className="h-5 w-5" />}
              title="Importez vos données"
              description="Uploadez votre CSV de feedbacks et commandes. Format simple, en 2 minutes."
            />
            <StepCard
              number="2"
              icon={<Brain className="h-5 w-5" />}
              title="L'IA analyse tout"
              description="Chaque feedback est classifié automatiquement — catégorie, sentiment, urgence, cause."
            />
            <StepCard
              number="3"
              icon={<BarChart3 className="h-5 w-5" />}
              title="Agissez sur les priorités"
              description="Vos problèmes sont classés par impact en euros. Vous savez exactement quoi corriger."
            />
          </div>
        </div>
      </section>

      {/* Métriques démo */}
      <section className="bg-zinc-900 py-20">
        <div className="mx-auto max-w-4xl px-8 text-center">
          <h2 className="text-2xl font-semibold text-white mb-4">
            Ce que vous verrez dans la démo
          </h2>
          <p className="text-zinc-400 mb-12">
            Données réelles générées à partir de 276 feedbacks et 500 commandes
          </p>
          <div className="grid grid-cols-2 gap-6 md:grid-cols-4 mb-12">
            <MetricCard value="118 937 €" label="CA associé aux problèmes" />
            <MetricCard value="5 808 €" label="Remboursements détectés" />
            <MetricCard value="44" label="Problèmes identifiés" />
            <MetricCard value="31" label="Clients à risque" />
          </div>
          <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-zinc-400 mb-10">
            {[
              "Problèmes de livraison",
              "Qualité produit",
              "Remboursements lents",
              "Service client",
              "Clients à risque élevé",
            ].map((item) => (
              <div key={item} className="flex items-center gap-1.5">
                <CheckCircle className="h-3.5 w-3.5 text-zinc-500" />
                {item}
              </div>
            ))}
          </div>
          <Button
            onClick={() => navigate('/dashboard')}
            size="lg"
            variant="outline"
            className="gap-2 border-zinc-700 text-white hover:bg-zinc-800 hover:text-white"
          >
            Accéder à la démo
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-100 py-8 text-center">
        <p className="text-sm text-zinc-400">
          CFRI — Customer Feedback Revenue Intelligence
        </p>
      </footer>
    </div>
  )
}

function ProblemCard({
  icon, title, description
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-6">
      <div className="mb-3">{icon}</div>
      <h3 className="font-semibold text-zinc-900 mb-2">{title}</h3>
      <p className="text-sm text-zinc-500">{description}</p>
    </div>
  )
}

function StepCard({
  number, icon, title, description
}: {
  number: string
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div className="text-center">
      <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-zinc-100 mb-4">
        {icon}
      </div>
      <div className="text-xs font-medium text-zinc-400 mb-1">
        Étape {number}
      </div>
      <h3 className="font-semibold text-zinc-900 mb-2">{title}</h3>
      <p className="text-sm text-zinc-500">{description}</p>
    </div>
  )
}

function MetricCard({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-lg bg-zinc-800 p-5">
      <p className="text-2xl font-bold text-white mb-1">{value}</p>
      <p className="text-xs text-zinc-400">{label}</p>
    </div>
  )
}