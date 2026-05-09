// TypeScript interfaces for the Anime Visual Language Engine

export interface StyleAxisScore {
  score: number
  category: string
  description?: string
}

export interface StyleAxesResponse {
  axes: StyleAxis[]
  categories: string[]
}

export interface StyleAxis {
  id: string
  category: string
  name: string
  prompt_positive: string
  prompt_negative?: string
  description?: string
  created_at: string
}

export interface ImageAnalyzeResponse {
  keyframe_id?: string
  style_axes: Record<string, number>
  style_axes_by_category: Record<string, Record<string, number>>
  generated_prompt: string
  confidence?: number
  similar_frames: SimilarFrameInResponse[]
}

export interface SimilarFrameInResponse {
  id: string
  path?: string
  anime?: string
  score: number
}

export interface SimilarFrame {
  id: string
  path?: string
  anime?: string
  studio?: string
  score: number
  style_axes?: Record<string, number>
}

export interface StyleSpaceFrame {
  id: string
  x: number
  y: number
  z?: number
  anime?: string
  studio?: string
  cluster_id?: string
  cluster_color?: string
  path?: string
}

export interface StyleSpaceCluster {
  id: string
  name?: string
  color?: string
  size: number
  representative_frame_id?: string
}

export interface StyleSpaceResponse {
  frames: StyleSpaceFrame[]
  clusters: StyleSpaceCluster[]
  total: number
}

export interface PromptGenerateRequest {
  keyframe_id?: string
  style_axes?: Record<string, number>
  max_words?: number
}

export interface PromptGenerateResponse {
  prompt: string
  confidence?: number
  llm_provider: string
  style_axes_used?: Record<string, number>
}

export interface Job {
  id: string
  job_type: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  error?: string
  created_at: string
}

export interface Keyframe {
  id: string
  path: string
  anime?: string
  studio?: string
  director?: string
  year?: number
  timestamp?: number
  width?: number
  height?: number
}

// Category color mapping for visual display
export const CATEGORY_COLORS: Record<string, string> = {
  COLOR: '#FF6B6B',
  LIGHTING: '#FFD93D',
  COMPOSITION: '#6BCB77',
  DIRECTING: '#4D96FF',
}

// Category labels (localized)
export const CATEGORY_LABELS: Record<string, string> = {
  COLOR: '色彩',
  LIGHTING: '光影',
  COMPOSITION: '构图',
  DIRECTING: '演出',
}

// All axis names for a category
export const AXIS_LABELS: Record<string, string> = {
  warm: '暖色调',
  cold: '冷色调',
  neon: '霓虹色',
  pastel: '马卡龙',
  low_saturation: '低饱和',
  cinematic_light: '电影光',
  soft_light: '柔光',
  hard_shadow: '硬阴影',
  rim_light: '轮廓光',
  film_grain: '胶片感',
  negative_space: '留白',
  dutch_angle: '斜角',
  centered: '中心',
  wide_shot: '全景',
  close_up: '特写',
  experimental: '实验性',
  cinematic: '电影感',
  melancholic: '忧郁感',
  surreal: '超现实',
  energetic: '高能动态',
  shaft_like: 'SHAFT风',
}
