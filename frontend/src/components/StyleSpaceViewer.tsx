import { useRef, useEffect, useState, useCallback } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import type { StyleSpaceFrame, StyleSpaceCluster } from '../types'

interface StyleSpaceViewerProps {
  frames: StyleSpaceFrame[]
  clusters: StyleSpaceCluster[]
  onFrameSelect?: (frame: StyleSpaceFrame) => void
  selectedFrameId?: string | null
  width?: number
  height?: number
}

export function StyleSpaceViewer({
  frames,
  clusters,
  onFrameSelect,
  selectedFrameId,
  width = 800,
  height = 600,
}: StyleSpaceViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [tooltip, setTooltip] = useState<{ x: number; y: number; frame: StyleSpaceFrame } | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || frames.length === 0) return

    // Scene setup
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x0a0a12)

    // Camera
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000)
    camera.position.set(0, 2, 5)

    // Renderer
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.05
    controls.maxDistance = 20

    // Lighting
    scene.add(new THREE.AmbientLight(0xffffff, 0.4))
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.6)
    dirLight.position.set(5, 5, 5)
    scene.add(dirLight)

    // Points
    const positions = new Float32Array(frames.length * 3)
    const colors = new Float32Array(frames.length * 3)
    const frameMap = new Map<number, StyleSpaceFrame>()

    frames.forEach((frame, i) => {
      positions[i * 3] = frame.x
      positions[i * 3 + 1] = frame.y
      positions[i * 3 + 2] = frame.z || 0

      const color = frame.cluster_color
        ? new THREE.Color(frame.cluster_color)
        : new THREE.Color(0x5680f9)
      colors[i * 3] = color.r
      colors[i * 3 + 1] = color.g
      colors[i * 3 + 2] = color.b

      frameMap.set(i, frame)
    })

    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))

    const material = new THREE.PointsMaterial({
      size: 0.08,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      sizeAttenuation: true,
    })

    const points = new THREE.Points(geometry, material)
    scene.add(points)

    // Raycasting for hover
    const raycaster = new THREE.Raycaster()
    const mouse = new THREE.Vector2()

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect()
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1

      raycaster.setFromCamera(mouse, camera)
      const intersects = raycaster.intersectObject(points)

      if (intersects.length > 0) {
        const idx = intersects[0].index!
        const frame = frameMap.get(idx)
        if (frame) {
          setTooltip({ x: e.clientX, y: e.clientY, frame })
          document.body.style.cursor = 'pointer'
        }
      } else {
        setTooltip(null)
        document.body.style.cursor = 'default'
      }
    }

    const handleClick = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect()
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1

      raycaster.setFromCamera(mouse, camera)
      const intersects = raycaster.intersectObject(points)

      if (intersects.length > 0) {
        const idx = intersects[0].index!
        const frame = frameMap.get(idx)
        if (frame && onFrameSelect) {
          onFrameSelect(frame)
        }
      }
    }

    canvas.addEventListener('mousemove', handleMouseMove)
    canvas.addEventListener('click', handleClick)

    // Animation loop
    let animId: number
    const animate = () => {
      animId = requestAnimationFrame(animate)
      controls.update()
      renderer.render(scene, camera)
    }
    animate()

    return () => {
      cancelAnimationFrame(animId)
      canvas.removeEventListener('mousemove', handleMouseMove)
      canvas.removeEventListener('click', handleClick)
      document.body.style.cursor = 'default'
      renderer.dispose()
      geometry.dispose()
      material.dispose()
    }
  }, [frames, width, height])

  return (
    <div className="relative w-full" style={{ height }}>
      <canvas ref={canvasRef} className="w-full h-full rounded-xl" />

      {tooltip && (
        <div
          className="absolute pointer-events-none z-10 glass-card px-3 py-2 text-xs"
          style={{
            left: tooltip.x + 12,
            top: tooltip.y - 40,
          }}
        >
          <div className="font-medium text-white">{tooltip.frame.anime || 'Unknown'}</div>
          {tooltip.frame.studio && (
            <div className="text-slate-400">{tooltip.frame.studio}</div>
          )}
        </div>
      )}

      {frames.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center text-slate-500">
          暂无数据 · 上传动画帧后在风格地图中查看
        </div>
      )}

      {/* Legend */}
      {clusters.length > 0 && (
        <div className="absolute top-4 right-4 glass-card p-3 text-xs space-y-1">
          <div className="font-medium text-slate-300 mb-2">聚类</div>
          {clusters.map((cluster) => (
            <div key={cluster.id} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: cluster.color || '#9E9E9E' }}
              />
              <span className="text-slate-400">
                {cluster.name || `Cluster ${cluster.id.slice(0, 6)}`}
                <span className="ml-1 text-slate-600">({cluster.size})</span>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
