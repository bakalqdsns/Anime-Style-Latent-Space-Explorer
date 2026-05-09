import { useState, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import { FileUploader } from '../components/FileUploader'
import { StyleAxisRadar } from '../components/StyleAxisRadar'
import { StyleAxisBar } from '../components/StyleAxisBar'
import { PromptCard } from '../components/PromptCard'
import { SimilarFrames } from '../components/SimilarFrames'
import { analyzeImage } from '../api/client'
import type { ImageAnalyzeResponse } from '../types'
import { CATEGORY_LABELS } from '../types'

export function Analyze() {
  const [preview, setPreview] = useState<string | null>(null)
  const [result, setResult] = useState<ImageAnalyzeResponse | null>(null)

  const mutation = useMutation({
    mutationFn: analyzeImage,
    onSuccess: (data) => {
      setResult(data)
    },
  })

  const handleFileSelect = useCallback((file: File) => {
    const url = URL.createObjectURL(file)
    setPreview(url)
    setResult(null)
    mutation.mutate(file)
  }, [mutation])

  const categories = result ? Object.entries(result.style_axes_by_category) : []

  return (
    <div className="min-h-screen bg-dark-400 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">图片分析</h1>
          <p className="text-slate-400">上传任意动漫截图，获取视觉风格分析</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left: Upload + Preview */}
          <div className="space-y-6">
            {!preview ? (
              <FileUploader onFileSelect={handleFileSelect} className="h-64" />
            ) : (
              <div className="space-y-4">
                <div className="relative rounded-xl overflow-hidden bg-dark-200">
                  <img
                    src={preview}
                    alt="Preview"
                    className="w-full max-h-96 object-contain"
                  />
                  {mutation.isPending && (
                    <div className="absolute inset-0 bg-dark-400/60 flex items-center justify-center">
                      <div className="text-center">
                        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                        <p className="text-sm text-slate-300">分析中...</p>
                      </div>
                    </div>
                  )}
                </div>
                <button
                  onClick={() => { setPreview(null); setResult(null) }}
                  className="text-sm text-slate-400 hover:text-white transition-colors"
                >
                  ← 重新上传
                </button>
              </div>
            )}

            {/* Error */}
            {mutation.isError && (
              <div className="glass-card p-4 border-red-500/30">
                <p className="text-red-400 text-sm">
                  分析失败: {mutation.error instanceof Error ? mutation.error.message : 'Unknown error'}
                </p>
              </div>
            )}
          </div>

          {/* Right: Results */}
          <div className="space-y-6">
            {result && (
              <>
                {/* Category Radar Charts */}
                <div className="glass-card p-6 animate-fade-in">
                  <h3 className="text-lg font-semibold text-white mb-4">风格轴分析</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {categories.map(([category, axes]) => (
                      <div key={category}>
                        <div className="flex items-center gap-2 mb-2">
                          <span
                            className="text-xs font-medium px-2 py-0.5 rounded"
                            style={{
                              backgroundColor: `rgba(86, 128, 249, 0.15)`,
                              color: '#78a2ff',
                            }}
                          >
                            {CATEGORY_LABELS[category] || category}
                          </span>
                        </div>
                        <StyleAxisRadar data={axes} category={category} />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Overall Score Bar Chart */}
                <div className="glass-card p-6 animate-fade-in">
                  <h3 className="text-lg font-semibold text-white mb-4">全部轴得分</h3>
                  <StyleAxisBar data={result.style_axes} />
                </div>

                {/* Generated Prompt */}
                <div className="animate-fade-in">
                  <h3 className="text-lg font-semibold text-white mb-4">生成 Prompt</h3>
                  <PromptCard
                    prompt={{
                      prompt: result.generated_prompt,
                      confidence: result.confidence ?? undefined,
                      llm_provider: 'style_analysis',
                      style_axes_used: result.style_axes,
                    }}
                  />
                </div>

                {/* Similar Frames */}
                {result.similar_frames.length > 0 && (
                  <div className="glass-card p-6 animate-fade-in">
                    <h3 className="text-lg font-semibold text-white mb-4">相似帧</h3>
                    <SimilarFrames frames={result.similar_frames} />
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
