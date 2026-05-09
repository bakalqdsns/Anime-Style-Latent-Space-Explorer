import { useState, useCallback } from 'react'
import { StyleAxisBar } from '../components/StyleAxisBar'
import { PromptCard } from '../components/PromptCard'
import { generatePrompt } from '../api/client'
import { CATEGORY_LABELS, CATEGORY_COLORS } from '../types'
import type { PromptGenerateResponse } from '../types'

// Default style axes with neutral scores
const DEFAULT_AXES: Record<string, Record<string, number>> = {
  COLOR: { warm: 0, cold: 0, neon: 0, pastel: 0, low_saturation: 0 },
  LIGHTING: { cinematic_light: 0, soft_light: 0, hard_shadow: 0, rim_light: 0, film_grain: 0 },
  COMPOSITION: { negative_space: 0, dutch_angle: 0, centered: 0, wide_shot: 0, close_up: 0 },
  DIRECTING: { experimental: 0, cinematic: 0, melancholic: 0, surreal: 0, energetic: 0, shaft_like: 0 },
}

export function PromptLab() {
  const [axes, setAxes] = useState(DEFAULT_AXES)
  const [prompt, setPrompt] = useState<PromptGenerateResponse | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  const handleSliderChange = useCallback(
    (category: string, axis: string, value: number) => {
      setAxes((prev) => ({
        ...prev,
        [category]: { ...prev[category], [axis]: value },
      }))
      setPrompt(null)
    },
    [],
  )

  const handleGenerate = useCallback(async () => {
    setIsGenerating(true)
    try {
      // Flatten axes to simple dict
      const flatAxes: Record<string, number> = {}
      for (const cat of Object.keys(axes)) {
        for (const [name, score] of Object.entries(axes[cat])) {
          flatAxes[name] = score
        }
      }

      const result = await generatePrompt(flatAxes, 50)
      setPrompt(result)
    } catch (err) {
      console.error('Prompt generation failed:', err)
    } finally {
      setIsGenerating(false)
    }
  }, [axes])

  const allAxesFlat = Object.values(axes).flatMap((cat) => Object.entries(cat))
  const activeAxes = Object.fromEntries(allAxesFlat)

  return (
    <div className="min-h-screen bg-dark-400 p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Prompt 实验室</h1>
          <p className="text-slate-400">
            拖动滑块调整风格轴，生成 AI 图像生成 Prompt
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left: Axis Sliders */}
          <div className="space-y-6">
            {Object.entries(axes).map(([category, categoryAxes]) => (
              <div key={category} className="glass-card p-6">
                <div className="flex items-center gap-2 mb-4">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: CATEGORY_COLORS[category] }}
                  />
                  <h3 className="text-lg font-semibold text-white">
                    {CATEGORY_LABELS[category] || category}
                  </h3>
                  <span className="text-xs text-slate-500">{category}</span>
                </div>

                <div className="space-y-4">
                  {Object.entries(categoryAxes).map(([axis, score]) => (
                    <div key={axis}>
                      <div className="flex items-center justify-between mb-1">
                        <label className="text-sm text-slate-300">
                          {axis.replace(/_/g, ' ')}
                        </label>
                        <span
                          className="text-xs font-mono"
                          style={{
                            color: score > 0 ? CATEGORY_COLORS[category] : score < 0 ? '#94a3b8' : '#64748b',
                          }}
                        >
                          {score > 0 ? '+' : ''}{score.toFixed(2)}
                        </span>
                      </div>
                      <input
                        type="range"
                        min={-1}
                        max={1}
                        step={0.05}
                        value={score}
                        onChange={(e) =>
                          handleSliderChange(category, axis, parseFloat(e.target.value))
                        }
                        className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
                        style={{
                          background: `linear-gradient(to right, #64748b 0%, ${CATEGORY_COLORS[category]} ${
                            ((score + 1) / 2) * 100
                          }%, ${CATEGORY_COLORS[category]} 100%)`,
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}

            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="w-full py-3 rounded-xl bg-primary-500 hover:bg-primary-600 disabled:opacity-50 text-white font-medium transition-colors flex items-center justify-center gap-2"
            >
              {isGenerating ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  生成中...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  生成 Prompt
                </>
              )}
            </button>
          </div>

          {/* Right: Results */}
          <div className="space-y-6">
            {/* Bar Chart */}
            <div className="glass-card p-6">
              <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
                当前轴配置
              </h3>
              <StyleAxisBar data={activeAxes} />
            </div>

            {/* Generated Prompt */}
            {prompt && (
              <div className="animate-slide-up">
                <PromptCard
                  prompt={prompt}
                  onRegenerate={handleGenerate}
                  isLoading={isGenerating}
                />
              </div>
            )}

            {/* Tips */}
            <div className="glass-card p-5">
              <h4 className="text-sm font-medium text-slate-400 mb-3">使用提示</h4>
              <ul className="text-xs text-slate-500 space-y-1.5">
                <li>· 正值 (+) = 增加该风格特征</li>
                <li>· 负值 (-) = 减少该风格特征</li>
                <li>· 值为 0 = 不影响该轴</li>
                <li>· 建议同时调整 3-5 个轴以获得最佳效果</li>
                <li>· 生成后可将 Prompt 复制到 Midjourney / Stable Diffusion</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
