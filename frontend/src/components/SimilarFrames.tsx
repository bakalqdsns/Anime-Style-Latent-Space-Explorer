import clsx from 'clsx'
import type { SimilarFrame } from '../types'

interface SimilarFramesProps {
  frames: SimilarFrame[]
  onSelect?: (frame: SimilarFrame) => void
  isLoading?: boolean
}

export function SimilarFrames({ frames, onSelect, isLoading }: SimilarFramesProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="aspect-video rounded-lg bg-dark-200 animate-pulse"
          />
        ))}
      </div>
    )
  }

  if (frames.length === 0) {
    return (
      <div className="text-center text-slate-500 py-8">
        暂无相似帧 · 继续添加动画数据后会自动匹配
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
      {frames.map((frame) => (
        <div
          key={frame.id}
          onClick={() => onSelect?.(frame)}
          className={clsx(
            'group relative aspect-video rounded-lg overflow-hidden bg-dark-200 cursor-pointer',
            'border border-white/5 hover:border-primary-500/40 transition-all',
          )}
        >
          {frame.path ? (
            <img
              src={`/frames/${frame.path.split('/').pop()}`}
              alt={frame.anime || 'frame'}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-slate-600">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          )}

          {/* Score overlay */}
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-white/80 truncate">
                {frame.anime || 'Unknown'}
              </span>
              <span className="text-xs font-mono text-primary-300">
                {(frame.score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
