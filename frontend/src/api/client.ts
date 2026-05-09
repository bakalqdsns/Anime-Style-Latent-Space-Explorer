import axios from 'axios'
import type {
  ImageAnalyzeResponse,
  StyleSpaceResponse,
  PromptGenerateResponse,
  StyleAxesResponse,
} from '../types'

const API_BASE = '/api'

const client = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─── Analyze ────────────────────────────────────────────────────────────────

export async function analyzeImage(file: File): Promise<ImageAnalyzeResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await client.post<ImageAnalyzeResponse>('/analyze/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
  return response.data
}

export async function analyzeImageUrl(url: string): Promise<ImageAnalyzeResponse> {
  const response = await client.post<ImageAnalyzeResponse>('/analyze/image-url', {
    url,
  })
  return response.data
}

// ─── Style Axes ──────────────────────────────────────────────────────────────

export async function fetchStyleAxes(): Promise<StyleAxesResponse> {
  const response = await client.get<StyleAxesResponse>('/style/axes')
  return response.data
}

export async function fetchStyleSpace(params?: {
  anime?: string
  cluster_id?: string
  limit?: number
}): Promise<StyleSpaceResponse> {
  const response = await client.get<StyleSpaceResponse>('/style/space', { params })
  return response.data
}

// ─── Prompt ─────────────────────────────────────────────────────────────────

export async function generatePrompt(
  styleAxes: Record<string, number>,
  maxWords: number = 50,
): Promise<PromptGenerateResponse> {
  const response = await client.post<PromptGenerateResponse>('/prompt/generate', {
    style_axes: styleAxes,
    max_words: maxWords,
  })
  return response.data
}

export async function generatePromptByKeyframe(
  keyframeId: string,
  maxWords: number = 50,
): Promise<PromptGenerateResponse> {
  const response = await client.post<PromptGenerateResponse>('/prompt/generate', {
    keyframe_id: keyframeId,
    max_words: maxWords,
  })
  return response.data
}

// ─── Similar Frames ─────────────────────────────────────────────────────────

export async function searchSimilar(
  embedding: number[],
  limit: number = 10,
  anime?: string,
): Promise<{ similar: import('../types').SimilarFrame[] }> {
  const response = await client.post<{ similar: import('../types').SimilarFrame[] }>(
    '/similar/by-embedding',
    { embedding, limit, anime },
  )
  return response.data
}

// ─── Health ─────────────────────────────────────────────────────────────────

export async function healthCheck(): Promise<{ status: string }> {
  const response = await client.get<{ status: string }>('/health')
  return response.data
}
