import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip,
} from 'recharts'
import { CATEGORY_COLORS } from '../types'

interface StyleAxisRadarProps {
  data: Record<string, number>
  category?: string
}

export function StyleAxisRadar({ data, category }: StyleAxisRadarProps) {
  const chartData = Object.entries(data).map(([axis, score]) => ({
    axis: axis.replace(/_/g, ' '),
    score: Math.round(((score + 1) / 2) * 100), // normalize -1..1 → 0..100
    fullMark: 100,
  }))

  const color = category ? CATEGORY_COLORS[category] || '#5680F9' : '#5680F9'

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="rgba(255,255,255,0.1)" />
          <PolarAngleAxis
            dataKey="axis"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            tickLine={false}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fill: '#64748b', fontSize: 10 }}
            tickCount={4}
            axisLine={false}
          />
          <Radar
            name="Style"
            dataKey="score"
            stroke={color}
            fill={color}
            fillOpacity={0.25}
            strokeWidth={2}
            dot={{ r: 3, fill: color }}
          />
          <Tooltip
            formatter={(value: number) => [`${value}%`, 'Style Score']}
            labelStyle={{ color: '#e2e8f0' }}
            contentStyle={{
              backgroundColor: 'rgba(30,30,47,0.9)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
