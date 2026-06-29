import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { formatCurrency, categoryLabel } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table, TableBody, TableCell,
  TableHead, TableHeader, TableRow
} from '@/components/ui/table'
import { AlertTriangle } from 'lucide-react'

export default function ProblemsPage() {
  const { data: problems, isLoading } = useQuery({
    queryKey: ['problems'],
    queryFn: apiClient.getProblems,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-zinc-400 text-sm">Chargement...</p>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-zinc-900">
          Top Problèmes
        </h1>
        <p className="text-sm text-zinc-500 mt-1">
          Problèmes clients classés par impact business
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            {problems?.length ?? 0} problèmes détectés
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {!problems || problems.length === 0 ? (
            <p className="text-sm text-zinc-400 py-8 text-center">
              Aucun problème détecté — importez des feedbacks et lancez l'analyse
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Problème</TableHead>
                  <TableHead className="text-center">Feedbacks</TableHead>
                  <TableHead className="text-center">Clients</TableHead>
                  <TableHead className="text-right">CA associé</TableHead>
                  <TableHead className="text-right">Remboursements</TableHead>
                  <TableHead className="text-center">Négatifs</TableHead>
                  <TableHead className="text-right">Score</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {problems.map((problem) => (
                  <TableRow key={problem.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium text-zinc-900 text-sm">
                          {problem.title}
                        </p>
                        <Badge variant="secondary" className="text-xs mt-1">
                          {categoryLabel(problem.category)}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell className="text-center text-sm">
                      {problem.feedback_count}
                    </TableCell>
                    <TableCell className="text-center text-sm">
                      {problem.customers_count}
                    </TableCell>
                    <TableCell className="text-right text-sm">
                      {formatCurrency(problem.associated_revenue)}
                    </TableCell>
                    <TableCell className="text-right text-sm text-red-600">
                      {problem.refund_amount > 0
                        ? formatCurrency(problem.refund_amount)
                        : '—'}
                    </TableCell>
                    <TableCell className="text-center">
                      <span className={`text-sm font-medium ${
                        problem.negative_rate > 75
                          ? 'text-red-600'
                          : problem.negative_rate > 40
                          ? 'text-orange-500'
                          : 'text-green-600'
                      }`}>
                        {problem.negative_rate}%
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant="outline" className="text-xs">
                        {problem.impact_score}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}