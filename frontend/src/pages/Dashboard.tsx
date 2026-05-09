import { Link } from 'react-router-dom'

export function Dashboard() {
  return (
    <div className="min-h-screen bg-dark-400 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-white mb-2 text-glow">
            Anime Visual Language Engine
          </h1>
          <p className="text-slate-400 text-lg">
            动漫视觉风格空间分析 · DINOv2 + CLIP + UMAP
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <Link
            to="/analyze"
            className="glass-card p-8 hover:border-primary-500/30 transition-all group"
          >
            <div className="w-12 h-12 rounded-xl bg-primary-500/10 flex items-center justify-center mb-4 group-hover:bg-primary-500/20 transition-colors">
              <svg className="w-6 h-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">分析图片</h2>
            <p className="text-slate-400 text-sm">
              上传任意动漫截图，获取风格分析、轴评分、Prompt 反推
            </p>
          </Link>

          <Link
            to="/style-map"
            className="glass-card p-8 hover:border-green-500/30 transition-all group"
          >
            <div className="w-12 h-12 rounded-xl bg-green-500/10 flex items-center justify-center mb-4 group-hover:bg-green-500/20 transition-colors">
              <svg className="w-6 h-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">风格地图</h2>
            <p className="text-slate-400 text-sm">
              探索风格空间 3D 可视化，按聚类和风格轴筛选
            </p>
          </Link>

          <Link
            to="/prompt-lab"
            className="glass-card p-8 hover:border-purple-500/30 transition-all group"
          >
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center mb-4 group-hover:bg-purple-500/20 transition-colors">
              <svg className="w-6 h-6 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Prompt 实验室</h2>
            <p className="text-slate-400 text-sm">
              调整风格轴权重，生成 AI 图像生成 Prompt
            </p>
          </Link>
        </div>

        {/* Stats */}
        <div className="glass-card p-6 mb-8">
          <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">系统状态</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: '关键帧', value: '—', icon: '🎬' },
              { label: '动画作品', value: '—', icon: '📺' },
              { label: '聚类数量', value: '—', icon: '🗂️' },
              { label: '风格轴', value: '21', icon: '📊' },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl mb-1">{stat.icon}</div>
                <div className="text-2xl font-bold text-white">{stat.value}</div>
                <div className="text-xs text-slate-500">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Architecture diagram */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">处理流程</h3>
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {[
              { label: 'Image', color: 'text-blue-400' },
              { label: 'DINOv2', color: 'text-orange-400' },
              { label: 'W Matrix', color: 'text-yellow-400' },
              { label: 'CLIP', color: 'text-green-400' },
              { label: 'Style Axes', color: 'text-purple-400' },
              { label: 'UMAP', color: 'text-pink-400' },
              { label: 'Prompt', color: 'text-cyan-400' },
            ].map((step, i) => (
              <div key={step.label} className="flex items-center gap-2 flex-shrink-0">
                <div className={`px-4 py-2 rounded-lg bg-dark-300 font-mono text-sm ${step.color}`}>
                  {step.label}
                </div>
                {i < 6 && <span className="text-slate-600">→</span>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
