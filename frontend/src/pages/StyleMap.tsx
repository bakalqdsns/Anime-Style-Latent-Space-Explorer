import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { StyleSpaceViewer } from '../components/StyleSpaceViewer'
import { StyleAxisBar } from '../components/StyleAxisBar'
import { FrameGrid } from '../components/FrameGrid'
import { fetchStyleSpace } from '../api/client'
import type { StyleSpaceFrame } from '../types'

export function StyleMap() {
  const [selectedFrame, setSelectedFrame] = useState<StyleSpaceFrame | null>(null)
  const [filter, setFilter] = useState<'all' | 'anime' | 'cluster'>('all')
  const [animeFilter, setAnimeFilter] = useState<string>('')

  const { data, isLoading } = useQuery({
    queryKey: ['style-space', filter, animeFilter],
    queryFn: () => fetchStyleSpace({ anime: animeFilter || undefined, limit: 2000 }),
    staleTime: 5 * 60 * 1000,
  })

  const frames = data?.frames || []
  const clusters = data?.clusters || []

  // Filter frames by anime
  const filteredFrames = animeFilter
    ? frames.filter((f) => f.anime?.toLowerCase().includes(animeFilter.toLowerCase()))
    : frames

  // Get unique anime names
  const animeNames = [...new Set(frames.map((f) => f.anime).filter(Boolean))]

  return (
    <div className="min-h-screen bg-dark-400 flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-white/5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">风格地图</h1>
            <p className="text-slate-400 text-sm mt-1">
              3D 可视化 · {frames.length} 帧 · {clusters.length} 聚类
            </p>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-3">
            <input
              type="text"
              placeholder="按动画名称过滤..."
              value={animeFilter}
              onChange={(e) => setAnimeFilter(e.target.value)}
              className="px-3 py-2 rounded-lg bg-dark-200 border border-white/10 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary-500/50"
            />
            {animeNames.length > 0 && (
              <select
                value={animeFilter}
                onChange={(e) => setAnimeFilter(e.target.value)}
                className="px-3 py-2 rounded-lg bg-dark-200 border border-white/10 text-sm text-white focus:outline-none"
              >
                <option value="">全部动画</option>
                {animeNames.map((name) => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* 3D Viewer */}
        <div className="flex-1 relative">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center z-10 bg-dark-400/80">
              <div className="text-center">
                <div className="w-10 h-10 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                <p className="text-slate-400">加载风格空间...</p>
              </div>
            </div>
          )}

          <StyleSpaceViewer
            frames={filteredFrames}
            clusters={clusters}
            onFrameSelect={setSelectedFrame}
            selectedFrameId={selectedFrame?.id}
            height={700}
          />

          {/* Instructions */}
          <div className="absolute bottom-4 left-4 glass-card px-3 py-2 text-xs text-slate-500">
            拖拽旋转 · 滚轮缩放 · 点击选中
          </div>
        </div>

        {/* Sidebar */}
        {selectedFrame && (
          <div className="w-96 border-l border-white/5 p-4 overflow-y-auto">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-slate-300">选中帧详情</h3>
                <button
                  onClick={() => setSelectedFrame(null)}
                  className="text-slate-500 hover:text-white text-sm"
                >
                  ✕
                </button>
              </div>

              {/* Frame preview */}
              {selectedFrame.path && (
                <img
                  src={`/frames/${selectedFrame.path.split('/').pop()}`}
                  alt="Frame"
                  className="w-full rounded-lg"
                />
              )}

              {/* Frame info */}
              <div className="glass-card p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">动画</span>
                  <span className="text-white">{selectedFrame.anime || '—'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">工作室</span>
                  <span className="text-white">{selectedFrame.studio || '—'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">聚类</span>
                  <span
                    className="px-2 py-0.5 rounded text-xs"
                    style={{
                      backgroundColor: selectedFrame.cluster_color
                        ? `${selectedFrame.cluster_color}30`
                        : '#333',
                      color: selectedFrame.cluster_color || '#fff',
                    }}
                  >
                    {selectedFrame.cluster_id
                      ? `Cluster ${selectedFrame.cluster_id.slice(0, 6)}`
                      : '—'}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">坐标</span>
                  <span className="text-slate-300 font-mono text-xs">
                    ({selectedFrame.x.toFixed(2)}, {selectedFrame.y.toFixed(2)})
                  </span>
                </div>
              </div>

              {/* Nearby frames in cluster */}
              {selectedFrame.cluster_id && (
                <div>
                  <h4 className="text-sm font-medium text-slate-300 mb-2">同聚类帧</h4>
                  <FrameGrid
                    frames={frames
                      .filter(
                        (f) =>
                          f.cluster_id === selectedFrame.cluster_id &&
                          f.id !== selectedFrame.id,
                      )
                      .slice(0, 8)}
                    columns={2}
                    onSelect={setSelectedFrame}
                    selectedId={selectedFrame.id}
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
