import { useState, useCallback, useRef } from 'react'
import clsx from 'clsx'

interface FileUploaderProps {
  onFileSelect: (file: File) => void
  accept?: string
  className?: string
}

export function FileUploader({ onFileSelect, accept = 'image/*', className }: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      const file = e.dataTransfer.files[0]
      if (file) onFileSelect(file)
    },
    [onFileSelect],
  )

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) onFileSelect(file)
    },
    [onFileSelect],
  )

  return (
    <div
      className={clsx(
        'upload-zone flex flex-col items-center justify-center p-12 text-center',
        isDragging && 'drag-over',
        className,
      )}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={handleChange}
      />

      <svg
        className="w-16 h-16 mb-4 text-primary-400 opacity-60"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
        />
      </svg>

      <p className="text-lg font-medium text-slate-300 mb-1">拖拽图片到此处</p>
      <p className="text-sm text-slate-500">或点击选择文件 · 支持 JPG, PNG, WEBP</p>
    </div>
  )
}
