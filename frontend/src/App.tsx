import { useEffect, useRef, useState } from 'react'

export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [width, setWidth] = useState('')
  const [height, setHeight] = useState('')
  const [format, setFormat] = useState('jpeg')
  const [error, setError] = useState('')
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

  useEffect(() => () => {
    const owner = previewOwner.current
    if (owner) {
      owner.image.onload = null
      owner.image.onerror = null
      URL.revokeObjectURL(owner.url)
      previewOwner.current = null
    }
  }, [])

  function selectFile(selected: File | null) {
    releasePreview()
    setFile(null)
    setWidth('')
    setHeight('')
    setFormat('jpeg')
    setError('')
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
          <form className="rounded-2xl border border-line bg-surface p-6 sm:p-8" onSubmit={(event) => event.preventDefault()}>
            <label htmlFor="image" className="mb-2 block text-sm font-semibold">Choose an image</label>
            <input ref={fileInput} id="image" type="file" accept="image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif" aria-describedby="file-help file-error" aria-invalid={Boolean(error)} onChange={(event) => selectFile(event.target.files?.[0] ?? null)} className="block w-full min-w-0 rounded-xl border border-dashed border-line bg-canvas p-4 text-sm text-muted file:mr-3 file:rounded-lg file:border-0 file:bg-ink file:px-4 file:py-2 file:font-medium file:text-white" />
            <p id="file-help" className="mt-2 text-xs text-muted">A preview appears when your browser supports the image.</p>
            <p id="file-error" role="alert" className="mt-2 text-sm text-danger">{error}</p>
            <fieldset disabled={!file} className="mt-7 disabled:opacity-50">
              <legend className="mb-3 text-sm font-semibold">Maximum dimensions <span className="font-normal text-muted">· optional</span></legend>
              <div className="grid grid-cols-2 gap-4">
                <div><label htmlFor="width" className="mb-2 block text-sm">Width (px)</label><input id="width" inputMode="numeric" value={width} onChange={(event) => setWidth(event.target.value)} placeholder="Original" aria-describedby="dimension-help" className="field" /></div>
                <div><label htmlFor="height" className="mb-2 block text-sm">Height (px)</label><input id="height" inputMode="numeric" value={height} onChange={(event) => setHeight(event.target.value)} placeholder="Original" aria-describedby="dimension-help" className="field" /></div>
              </div>
              <p id="dimension-help" className="mt-2 text-xs leading-relaxed text-muted">Leave either blank to keep it unconstrained. The whole image fits within your limits.</p>
              <label htmlFor="format" className="mb-2 mt-6 block text-sm font-semibold">Output format</label>
              <select id="format" value={format} onChange={(event) => setFormat(event.target.value)} className="field"><option value="jpeg">JPEG</option><option value="png">PNG</option><option value="webp">WebP</option></select>
            </fieldset>
            <div className="mt-4 space-y-2 text-xs leading-relaxed text-muted">
              {format === 'jpeg' && <p>If the image has transparency, JPEG turns it white.</p>}
              <p>HEIC: only the primary image is kept. Extra images are omitted; HDR becomes ordinary 8-bit output.</p>
            </div>
            <button type="button" disabled={!file} className="mt-7 w-full rounded-xl bg-accent px-5 py-4 text-sm font-semibold text-white transition-colors hover:bg-ink disabled:cursor-not-allowed disabled:opacity-40">Process image</button>
            <p className="mt-3 text-center text-xs text-muted">Your result downloads automatically.</p>
          </form>
        </section>
      </div>
    </main>
  )
}
