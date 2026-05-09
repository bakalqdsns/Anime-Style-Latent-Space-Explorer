import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts'
import { AXIS_LABELS, CATEGORY_COLORS } from '../types'

interface StyleAxisBarProps {
  data: Record<string, number>
  category?: string
}

export function StyleAxisBar({ data, category }: StyleAxisBarProps) {
  const chartData = Object.entries(data)
    .map(([name, score]) => ({
      name: AXIS_LABELS[name] || name.replace(/_/g, ' '),
      score: Math.round(score * 100) / 100,
      rawName: name,
    }))
    .sort((a, b) => b.score - a.score)

  const color = category ? CATEGORY_COLORS[category] || '#5680F9' : '#5680F9'

  if (chartData.length === 0) return null

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical" margin={{ right: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
          <XAxis
            type="number"
            domain={[-1, 1]}
            tick={{ fill: '#64748b', fontSize: 10 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            width={70}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            formatter={(value: number) => [value.toFixed(2), 'Score']}
            labelStyle={{ color: '#e2e8f0' }}
            contentStyle={{
              backgroundColor: 'rgba(30,30,47,0.9)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
            }}
            cursor={{ fill: 'rgba(255,255,255,0.03)' }}
          />
          <Bar dataKey="score" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.score > 0 ? color : 'rgba(255,255,255,0.15)'}
                fillOpacity={0.7}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
