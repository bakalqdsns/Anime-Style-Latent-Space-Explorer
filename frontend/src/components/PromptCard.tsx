import { useState } from 'react'
import clsx from 'clsx'
import type { PromptGenerateResponse } from '../types'

interface PromptCardProps {
  prompt: PromptGenerateResponse
  onRegenerate?: () => void
  isLoading?: boolean
}

export function PromptCard({ prompt, onRegenerate, isLoading }: PromptCardProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(prompt.prompt)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="glass-card p-5 animate-slide-up">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-primary-500/20 text-primary-300">
            {prompt.llm_provider}
          </span>
          {prompt.confidence !== undefined && (
            <span className="text-xs text-slate-500">
              confidence: {Math.round(prompt.confidence * 100)}%
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className={clsx(
              'text-xs px-3 py-1.5 rounded-lg transition-all',
              copied
                ? 'bg-green-500/20 text-green-400'
                : 'bg-dark-200 hover:bg-dark-100 text-slate-400 hover:text-white',
            )}
          >
            {copied ? '✓ Copied' : 'Copy'}
          </button>
          {onRegenerate && (
            <button
              onClick={onRegenerate}
              disabled={isLoading}
              className="text-xs px-3 py-1.5 rounded-lg bg-dark-200 hover:bg-dark-100 text-slate-400 hover:text-white transition-all disabled:opacity-50"
            >
              {isLoading ? '...' : 'Regenerate'}
            </button>
          )}
        </div>
      </div>

      <div
        className={clsx(
          'text-sm font-mono leading-relaxed p-4 rounded-lg',
          'bg-dark-300/50 border border-white/5',
          'text-slate-200',
        )}
      >
        {prompt.prompt}
      </div>
    </div>
  )
}
