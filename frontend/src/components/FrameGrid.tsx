import clsx from 'clsx'
import type { SimilarFrame } from '../types'

interface FrameGridProps {
  frames: SimilarFrame[]
  columns?: number
  onSelect?: (frame: SimilarFrame) => void
  selectedId?: string | null
}

export function FrameGrid({ frames, columns = 4, onSelect, selectedId }: FrameGridProps) {
  if (frames.length === 0) {
    return (
      <div className="text-center text-slate-500 py-12">
        暂无帧数据
      </div>
    )
  }

  return (
    <div
      className="grid gap-3"
      style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
    >
      {frames.map((frame) => (
        <div
          key={frame.id}
          onClick={() => onSelect?.(frame)}
          className={clsx(
            'group relative aspect-video rounded-lg overflow-hidden cursor-pointer',
            'bg-dark-200 transition-all',
            selectedId === frame.id
              ? 'ring-2 ring-primary-500 scale-[1.02]'
              : 'hover:ring-1 hover:ring-white/20',
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
            <div className="w-full h-full bg-dark-300 flex items-center justify-center">
              <span className="text-slate-600 text-xs">No preview</span>
            </div>
          )}

          {/* Hover info */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-2">
            <div className="text-xs text-white">
              <div className="font-medium">{frame.anime || 'Unknown'}</div>
              {frame.studio && <div className="text-white/60">{frame.studio}</div>}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
