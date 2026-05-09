import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { Analyze } from './pages/Analyze'
import { StyleMap } from './pages/StyleMap'
import { PromptLab } from './pages/PromptLab'

export default function App() {
  return (
    <BrowserRouter>
      {/* Top Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-card border-b border-white/5 px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-6">
            <a href="/" className="text-sm font-semibold text-white hover:text-primary-300 transition-colors">
              AVLEN
            </a>
            <div className="flex items-center gap-1">
              {[
                { path: '/', label: '首页' },
                { path: '/analyze', label: '分析' },
                { path: '/style-map', label: '风格地图' },
                { path: '/prompt-lab', label: 'Prompt 实验室' },
              ].map(({ path, label }) => (
                <a
                  key={path}
                  href={path}
                  className="text-sm px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-all"
                >
                  {label}
                </a>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            System Online
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="pt-14">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/style-map" element={<StyleMap />} />
          <Route path="/prompt-lab" element={<PromptLab />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
