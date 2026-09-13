import { useEffect, useRef, useState } from 'react'

export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [width, setWidth] = useState('')
  const [height, setHeight] = useState('')
  const [sizeLimit, setSizeLimit] = useState('')
  const [sizeUnit, setSizeUnit] = useState('mb')
  const [format, setFormat] = useState('jpeg')
  const [error, setError] = useState('')
  const [miss, setMiss] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)
  const [invalid, setInvalid] = useState<string[]>([])
  const operation = useRef<AbortController | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const previewOwner = useRef<{ url: string; image: HTMLImageElement } | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)

  function releasePreview() {
    const owner = previewOwner.current
    previewOwner.current = null
    if (owner) {
      owner.image.onload = null
      owner.image.onerror = null
      URL.revokeObjectURL(owner.url)
    }
    setPreview(null)
  }

  useEffect(() => {
    function abandon() {
      operation.current?.abort()
      operation.current = null
      const owner = previewOwner.current
      if (owner) {
        owner.image.onload = null
        owner.image.onerror = null
        URL.revokeObjectURL(owner.url)
        previewOwner.current = null
      }
      if (fileInput.current) fileInput.current.value = ''
      setFile(null)
      setPreview(null)
      setWidth('')
      setHeight('')
      setSizeLimit('')
      setSizeUnit('mb')
      setFormat('jpeg')
      setError('')
      setMiss(null)
      setInvalid([])
      setBusy(false)
    }
    window.addEventListener('pagehide', abandon)
    return () => {
      window.removeEventListener('pagehide', abandon)
      abandon()
    }
  }, [])

  function selectFile(selected: File | null) {
    const pending = operation.current
    operation.current = null
    setBusy(false)
    pending?.abort()
    releasePreview()
    setFile(null)
    setWidth('')
    setHeight('')
    setSizeLimit('')
    setSizeUnit('mb')
    setFormat('jpeg')
    setError('')
    setMiss(null)
    setInvalid([])
    if (!selected) return
    if (selected.size === 0 || selected.size > 20_000_000) {
      setError(selected.size === 0 ? 'Choose a non-empty image.' : 'Choose an image no larger than 20 MB.')
      return
    }
    setFile(selected)
    const owner = { url: URL.createObjectURL(selected), image: new Image() }
    previewOwner.current = owner
    owner.image.onload = () => {
      if (previewOwner.current === owner) setPreview(owner.url)
    }
    owner.image.onerror = () => {
      if (previewOwner.current === owner) releasePreview()
    }
    owner.image.src = owner.url
  }

  async function submit() {
    if (!file || operation.current) return
    const bad = [['max_width', width], ['max_height', height]]
      .filter(([, value]) => value !== '' && (!/^[0-9]+$/.test(value) || !/[1-9]/.test(value)))
      .map(([name]) => name)
    if (sizeLimit !== '' && (!/^(?:\d+\.?\d*|\.\d+)$/.test(sizeLimit) || !(Number(sizeLimit) > 0))) {
      bad.push('size_limit')
    }
    setInvalid(bad)
    setError('')
    setMiss(null)
    if (bad.length) {
      setError(bad.includes('size_limit')
        ? 'Size limit must be a positive number with Mb or Kb or left empty'
        : 'Dimensions must be positive whole pixel counts, or blank.')
      return
    }
    const current = new AbortController()
    operation.current = current
    setBusy(true)
    const body = new FormData()
    body.append('file', file)
    if (width) body.append('max_width', width)
    if (height) body.append('max_height', height)
    if (sizeLimit) {
      body.append('size_limit', sizeLimit)
      body.append('size_unit', sizeUnit)
    }
    body.append('output_format', format)
    try {
      const response = await fetch('/api/v1/images/process', { method: 'POST', body, signal: current.signal })
      if (!response.ok) {
        const fallback = response.status === 413 ? 'The image exceeds the file or pixel limit.'
          : response.status === 415 ? 'Choose a supported JPEG, PNG, WebP or HEIC image.'
          : response.status === 422 ? 'Check the image and processing settings.'
          : 'Processing failed. Please try again.'
        let message = fallback
        let fields: string[] = []
        const payload: unknown = await response.json().catch(() => null)
        if (payload && typeof payload === 'object' && 'detail' in payload) {
          const detail = payload.detail
          if (typeof detail === 'string') message = detail
          else if (Array.isArray(detail)) {
            const messages: string[] = []
            for (const entry of detail) {
              if (!entry || typeof entry !== 'object') continue
              if (typeof entry.msg === 'string') messages.push(entry.msg)
              if (Array.isArray(entry.loc)) fields = fields.concat(entry.loc.filter((name: unknown) =>
                typeof name === 'string' && ['file', 'max_width', 'max_height', 'output_format', 'size_limit', 'size_unit'].includes(name)))
            }
            if (messages.length) message = messages.join(' ')
          }
        }
        if (operation.current === current) {
          setInvalid(fields)
          setError(message)
        }
        return
      }
      const blob = await response.blob()
      if (operation.current !== current) return
      const url = URL.createObjectURL(blob)
      try {
        const link = document.createElement('a')
        link.href = url
        link.download = `result.${format === 'jpeg' ? 'jpg' : format}`
        document.body.append(link)
        try { link.click() } finally { link.remove() }
      } finally {
        URL.revokeObjectURL(url)
      }
      const header = response.headers.get('x-size-limit-met')
      const resultBytes = Number(response.headers.get('x-result-bytes')) || blob.size
      const met = !sizeLimit || header === 'true' || (header !== 'false'
        && blob.size <= Math.trunc(Number(sizeLimit) * (sizeUnit === 'mb' ? 1_000_000 : 1000)))
      if (met) {
        selectFile(null)
        if (fileInput.current) {
          fileInput.current.value = ''
          fileInput.current.disabled = false
          fileInput.current.focus()
        }
      } else {
        setMiss(resultBytes)
      }
    } catch {
      if (operation.current === current) setError('The transfer failed. Please try again.')
    } finally {
      if (operation.current === current) {
        operation.current = null
        setBusy(false)
      }
    }
  }

  return (
    <main className="mx-auto min-h-svh max-w-6xl px-5 py-10 sm:px-12 sm:py-16">
      <header className="mb-12 flex items-center justify-between border-b border-line pb-5">
        <p className="text-sm font-semibold tracking-tight">Image compressor<span className="text-accent">.</span></p>
        <span className="text-xs uppercase tracking-widest text-muted">One image. A better fit.</span>
      </header>
      <div className="grid items-start gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:gap-20">
        <section aria-labelledby="page-title" className="lg:sticky lg:top-12">
          <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-accent">Resize & convert</p>
          <h1 id="page-title" className="text-5xl font-semibold leading-tight tracking-tight sm:text-6xl">Make room.<br />Keep the picture.</h1>
          <p className="mt-6 max-w-sm text-lg leading-relaxed text-muted">Give your image the dimensions and format it needs. We’ll keep the proportions.</p>
          <p className="mt-8 max-w-sm text-sm leading-relaxed text-muted">JPEG, PNG, WebP or HEIC · Up to 20 MB<br />One image at a time. No cropping or enlargement.</p>
        </section>
        <section aria-label="Image settings" className="min-w-0">
          {preview && <div className="mb-5 overflow-hidden rounded-2xl border border-line bg-surface p-3"><img src={preview} alt="Selected image preview" className="mx-auto max-h-72 max-w-full object-contain" /></div>}
          <form className="rounded-2xl border border-line bg-surface p-6 sm:p-8" aria-busy={busy} onSubmit={(event) => { event.preventDefault(); void submit() }}>
            <label htmlFor="image" className="mb-2 block text-sm font-semibold">Choose an image</label>
            <input ref={fileInput} id="image" type="file" disabled={busy} accept="image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif" aria-describedby="file-help file-error" aria-invalid={invalid.includes('file') || (!file && Boolean(error))} onChange={(event) => selectFile(event.target.files?.[0] ?? null)} className="block w-full min-w-0 rounded-xl border border-dashed border-line bg-canvas p-4 text-sm text-muted file:mr-3 file:rounded-lg file:border-0 file:bg-ink file:px-4 file:py-2 file:font-medium file:text-white" />
            <p id="file-help" className="mt-2 text-xs text-muted">A preview appears when your browser supports the image.</p>
            <p id="file-error" role="alert" className="mt-2 break-all text-sm text-danger">{error}</p>
            {miss !== null && <p role="status" aria-live="polite" className="mt-2 text-sm">The result is {miss} bytes. The size limit was exceeded.</p>}
            <fieldset disabled={!file || busy} className="mt-7 disabled:opacity-50">
              <legend className="mb-3 text-sm font-semibold">Maximum dimensions <span className="font-normal text-muted">· optional</span></legend>
              <div className="grid grid-cols-2 gap-4">
                <div><label htmlFor="width" className="mb-2 block text-sm">Width (px)</label><input id="width" inputMode="numeric" value={width} onChange={(event) => setWidth(event.target.value)} placeholder="Original" aria-describedby="dimension-help file-error" aria-invalid={invalid.includes('max_width')} className="field" /></div>
                <div><label htmlFor="height" className="mb-2 block text-sm">Height (px)</label><input id="height" inputMode="numeric" value={height} onChange={(event) => setHeight(event.target.value)} placeholder="Original" aria-describedby="dimension-help file-error" aria-invalid={invalid.includes('max_height')} className="field" /></div>
              </div>
              <p id="dimension-help" className="mt-2 text-xs leading-relaxed text-muted">Leave either blank to keep it unconstrained. The whole image fits within your limits.</p>
              <label htmlFor="size-limit" className="mb-2 mt-6 block text-sm font-semibold">Size limit <span className="font-normal text-muted">· optional</span></label>
              <div className="flex min-w-0 items-center gap-3">
                <input id="size-limit" inputMode="decimal" value={sizeLimit} onChange={(event) => setSizeLimit(event.target.value)} placeholder="None" aria-describedby="size-limit-help file-error" aria-invalid={invalid.includes('size_limit')} className="field min-w-0 flex-1" />
                <select id="size-unit" aria-label="Size unit" aria-describedby="size-limit-help file-error" aria-invalid={invalid.includes('size_unit')} value={sizeUnit} onChange={(event) => setSizeUnit(event.target.value)} className="field w-auto shrink-0"><option value="mb">Mb</option><option value="kb">Kb</option></select>
              </div>
              <p id="size-limit-help" className="mt-2 text-xs leading-relaxed text-muted">Leave empty for no result size bound.</p>
              <label htmlFor="format" className="mb-2 mt-6 block text-sm font-semibold">Output format</label>
              <select id="format" aria-describedby="file-error" aria-invalid={invalid.includes('output_format')} value={format} onChange={(event) => setFormat(event.target.value)} className="field"><option value="jpeg">JPEG</option><option value="png">PNG</option><option value="webp">WebP</option></select>
            </fieldset>
            <div className="mt-4 space-y-2 text-xs leading-relaxed text-muted">
              {format === 'jpeg' && <p>If the image has transparency, JPEG turns it white.</p>}
              <p>HEIC: only the primary image is used; extra images are omitted. HDR becomes ordinary 8-bit output and may not retain its original appearance.</p>
            </div>
            <button type="submit" disabled={!file || busy} className="mt-7 w-full rounded-xl bg-accent px-5 py-4 text-sm font-semibold text-white transition-colors hover:bg-ink disabled:cursor-not-allowed disabled:opacity-40">{busy ? 'Processing…' : 'Process image'}</button>
            <p role="status" className="mt-3 text-center text-xs text-muted">{busy ? 'Processing your image…' : 'Your result downloads automatically.'}</p>
          </form>
        </section>
      </div>
    </main>
  )
}
