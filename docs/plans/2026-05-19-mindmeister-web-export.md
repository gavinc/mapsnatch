# MindMeister Web Export Service Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** A Vercel-hosted Next.js web app where non-technical MindMeister users paste their API token, select their maps, pay $5 via Stripe, and download a zip of all their maps in FreeMind (.mm) + PDF format.

**Architecture:** Next.js App Router, server-side API routes proxy all MindMeister calls (token never stored, lives only in the browser session via sessionStorage). Stripe Checkout for one-time $5 payment. No database — payment unlocks a signed session cookie that expires in 1 hour. JSZip bundles the export.

**Tech Stack:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Stripe (one-time checkout), `stripe` npm package, Vercel deployment, no database.

---

## ⚠️ Known caveat: maps with embedded images (read before implementing export)

**Discovered during CLI build and live testing.**

When MindMeister exports a map that contains embedded images (e.g. a map where the user has pasted screenshots or photos), the `.mm` endpoint returns a **zip file containing multiple entries** — the embedded images first, then the `.mm` file last:

```
Archive: Projects___Todos.zip
  561914  1000006705.jpg    ← first entry (image)
  678046  1000006706.jpg    ← second entry (image)
    7875  Projects___Todos.mm  ← actual map data
```

**The bug this causes:** naively taking the first entry from the zip (`zip.files[0]`) extracts a JPEG and saves it with a `.mm` extension. The file appears to export successfully but is corrupt.

**The fix in `unzipFirst` (see Task 4, `src/app/api/export/route.ts`):**

Replace the current `unzipFirst` implementation with one that finds the file matching the requested extension:

```typescript
async function extractTargetFromZip(buf: ArrayBuffer, fmt: string): Promise<ArrayBuffer> {
  try {
    const zip = await JSZip.loadAsync(buf)
    // Find the file matching the requested format, not just the first entry
    const target = Object.entries(zip.files).find(
      ([name, f]) => !f.dir && name.toLowerCase().endsWith(`.${fmt}`)
    )
    if (target) return await target[1].async('arraybuffer')
    // Fallback: first non-directory entry
    const first = Object.values(zip.files).find(f => !f.dir)
    if (first) return await first.async('arraybuffer')
  } catch { /* not a zip */ }
  return buf
}
```

**Also add post-save validation** — after writing each file to the zip, detect its content type by magic bytes and log a warning if it doesn't match the expected format. The Python CLI has `detect_content_type()` in `exporter.py` as a reference implementation. Magic bytes to check:

| Signature | Type |
|---|---|
| `\x89PNG` | PNG image (wrong for .mm) |
| `\xFF\xD8\xFF` | JPEG image (wrong for .mm) |
| `%PDF` | PDF (wrong for .mm) |
| `PK\x03\x04` | ZIP (ok for .xmind, wrong for .mm) |
| `<` | XML (correct for .mm, .mind) |

**Scope:** Affects all zipped formats (`mm`, `mind`, `xmind`). The `pdf` and `rtf` formats are direct (not zipped) and are unaffected.

---

## Security model (read before implementing)

- User's API token is **never written to any server-side storage** (no DB, no logs, no env).
- Token travels: `sessionStorage (browser)` → `Authorization header` → `Next.js API route` → `MindMeister API` → response back. Cleared when tab closes.
- Payment unlocks export via a **signed cookie** (`HMAC-SHA256` of `{sessionId}:{timestamp}`, verified server-side). Cookie expires in 1 hour.
- Rate limiting: Vercel Edge Middleware, 10 req/min per IP.

---

## Repo name

`meister-export-web` under `gavinc` GitHub account. Deploy to Vercel linked to that repo.

---

### Task 1: Next.js project scaffold

**Files:**
- Run: `npx create-next-app@latest meister-export-web --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --no-git`
- Create: `src/lib/mindmeister.ts`
- Create: `src/lib/payment.ts`
- Create: `.env.local.example`

**Step 1: Create the Next.js app**

```bash
cd /home/heavygee/coding
npx create-next-app@latest meister-export-web \
  --typescript --tailwind --eslint --app --src-dir \
  --import-alias "@/*" --no-git
cd meister-export-web
```

**Step 2: Install dependencies**

```bash
npm install stripe @stripe/stripe-js jszip
npm install -D @types/jszip
```

**Step 3: Write .env.local.example**

```
# Stripe — get from https://dashboard.stripe.com/apikeys
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...   # one-time $5 price created in Stripe dashboard

# Session signing key — generate with: openssl rand -hex 32
SESSION_SECRET=your_32_byte_hex_secret

# App URL
NEXT_PUBLIC_APP_URL=https://your-domain.vercel.app
```

**Step 4: Copy to .env.local and fill in test keys**

```bash
cp .env.local.example .env.local
# Edit .env.local with real Stripe test keys
```

**Step 5: Init git and first commit**

```bash
git init
git add .
git commit -m "chore: scaffold meister-export-web with Next.js 14"
```

---

### Task 2: MindMeister API client (TypeScript)

**Files:**
- Create: `src/lib/mindmeister.ts`
- Create: `src/lib/mindmeister.test.ts`

**Step 1: Write failing tests**

```typescript
// src/lib/mindmeister.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MindMeisterClient, type MapInfo } from './mindmeister'

global.fetch = vi.fn()

describe('MindMeisterClient', () => {
  beforeEach(() => vi.clearAllMocks())

  it('throws if token is empty', () => {
    expect(() => new MindMeisterClient('')).toThrow('token')
  })

  it('lists maps from v1 API', async () => {
    const mockResp = {
      rsp: {
        stat: 'ok',
        maps: {
          total: '2',
          map: [
            { id: '111', title: 'Map One', modified: '2026-01-01 10:00:00', owner: '42' },
            { id: '222', title: 'Map Two', modified: '2026-01-02 10:00:00', owner: '42' },
          ],
        },
      },
    }
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResp,
    } as Response)

    const client = new MindMeisterClient('test_token')
    const maps = await client.listMaps()
    expect(maps).toHaveLength(2)
    expect(maps[0].id).toBe('111')
    expect(maps[0].title).toBe('Map One')
  })

  it('sends Bearer auth header', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ rsp: { stat: 'ok', maps: { total: '0', map: [] } } }),
    } as Response)
    const client = new MindMeisterClient('my_secret_token')
    await client.listMaps()
    expect(vi.mocked(fetch).mock.calls[0][1]?.headers).toMatchObject({
      Authorization: 'Bearer my_secret_token',
    })
  })

  it('exports a map as bytes', async () => {
    const pdfBytes = new Uint8Array([0x25, 0x50, 0x44, 0x46])
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      arrayBuffer: async () => pdfBytes.buffer,
    } as unknown as Response)
    const client = new MindMeisterClient('test_token')
    const data = await client.exportMap('111', 'pdf')
    expect(data.byteLength).toBe(4)
  })
})
```

**Step 2: Add vitest**

```bash
npm install -D vitest @vitejs/plugin-react
```

Add to `package.json`:
```json
"scripts": {
  "test": "vitest run",
  "test:watch": "vitest"
}
```

**Step 3: Run tests to confirm fail**

```bash
npm test 2>&1 | head -20
```
Expected: Cannot find module `./mindmeister`

**Step 4: Implement mindmeister.ts**

```typescript
// src/lib/mindmeister.ts
const LIST_URL = 'https://www.mindmeister.com/services/rest/oauth2'
const API_V2 = 'https://www.mindmeister.com/api/v2'

export interface MapInfo {
  id: string
  title: string
  modified: string
  owner: string
}

export class MindMeisterClient {
  private token: string

  constructor(token: string) {
    if (!token) throw new Error('API token is required')
    this.token = token
  }

  private get headers() {
    return { Authorization: `Bearer ${this.token}` }
  }

  async listMaps(): Promise<MapInfo[]> {
    const url = new URL(LIST_URL)
    url.searchParams.set('method', 'mm.maps.getList')
    url.searchParams.set('output', 'json')

    const resp = await fetch(url.toString(), { headers: this.headers })
    if (!resp.ok) throw new Error(`MindMeister list error: ${resp.status}`)

    const data = await resp.json()
    if (data.rsp.stat !== 'ok') throw new Error(`API error: ${JSON.stringify(data.rsp)}`)

    const raw = data.rsp.maps.map
    const arr = Array.isArray(raw) ? raw : raw ? [raw] : []
    return arr.map((m: Record<string, string>) => ({
      id: m.id,
      title: m.title,
      modified: m.modified ?? '',
      owner: m.owner ?? '',
    }))
  }

  async exportMap(mapId: string, format: string): Promise<ArrayBuffer> {
    const url = format === 'png' || format === 'jpeg'
      ? `${API_V2}/map_images/${mapId}.${format}`
      : `${API_V2}/maps/${mapId}.${format}`

    const resp = await fetch(url, { headers: this.headers })
    if (!resp.ok) throw new Error(`Export failed: ${resp.status}`)
    return resp.arrayBuffer()
  }
}
```

**Step 5: Run tests — expect PASS**

```bash
npm test
```

**Step 6: Commit**

```bash
git add src/lib/mindmeister.ts src/lib/mindmeister.test.ts
git commit -m "feat: MindMeister API client in TypeScript"
```

---

### Task 3: Stripe payment flow

**Files:**
- Create: `src/lib/payment.ts`
- Create: `src/app/api/checkout/route.ts`
- Create: `src/app/api/verify-payment/route.ts`

**Step 1: Implement payment.ts (session signing)**

```typescript
// src/lib/payment.ts
import { createHmac } from 'crypto'

const SECRET = process.env.SESSION_SECRET!

export function signSession(sessionId: string): string {
  const ts = Date.now()
  const sig = createHmac('sha256', SECRET)
    .update(`${sessionId}:${ts}`)
    .digest('hex')
  return `${sessionId}:${ts}:${sig}`
}

export function verifySession(token: string): boolean {
  const parts = token.split(':')
  if (parts.length !== 3) return false
  const [sessionId, ts, sig] = parts
  const age = Date.now() - parseInt(ts)
  if (age > 3600_000) return false  // 1 hour expiry
  const expected = createHmac('sha256', SECRET)
    .update(`${sessionId}:${ts}`)
    .digest('hex')
  return sig === expected
}
```

**Step 2: Create checkout API route**

```typescript
// src/app/api/checkout/route.ts
import { NextResponse } from 'next/server'
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

export async function POST() {
  const session = await stripe.checkout.sessions.create({
    payment_method_types: ['card'],
    line_items: [{
      price: process.env.STRIPE_PRICE_ID!,
      quantity: 1,
    }],
    mode: 'payment',
    success_url: `${process.env.NEXT_PUBLIC_APP_URL}/export?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/`,
  })
  return NextResponse.json({ url: session.url })
}
```

**Step 3: Create verify-payment API route**

```typescript
// src/app/api/verify-payment/route.ts
import { NextRequest, NextResponse } from 'next/server'
import Stripe from 'stripe'
import { signSession } from '@/lib/payment'
import { cookies } from 'next/headers'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

export async function POST(req: NextRequest) {
  const { sessionId } = await req.json()
  const session = await stripe.checkout.sessions.retrieve(sessionId)

  if (session.payment_status !== 'paid') {
    return NextResponse.json({ error: 'Payment not completed' }, { status: 402 })
  }

  const signed = signSession(sessionId)
  const cookieStore = await cookies()
  cookieStore.set('export_session', signed, {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
    maxAge: 3600,
    path: '/',
  })

  return NextResponse.json({ ok: true })
}
```

**Step 4: Commit**

```bash
git add src/lib/payment.ts src/app/api/checkout/route.ts src/app/api/verify-payment/route.ts
git commit -m "feat: Stripe checkout and session signing"
```

---

### Task 4: Maps API routes (server-side proxy)

**Files:**
- Create: `src/app/api/maps/route.ts`
- Create: `src/app/api/export/route.ts`

These routes proxy MindMeister calls server-side so the user's token is never exposed in browser network requests to MindMeister directly. Token comes in the request header, used once, never stored.

**Step 1: Maps list proxy**

```typescript
// src/app/api/maps/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { MindMeisterClient } from '@/lib/mindmeister'

export async function GET(req: NextRequest) {
  const token = req.headers.get('x-mm-token')
  if (!token) return NextResponse.json({ error: 'No token' }, { status: 401 })

  try {
    const client = new MindMeisterClient(token)
    const maps = await client.listMaps()
    return NextResponse.json({ maps })
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
```

**Step 2: Export proxy (streams zip)**

```typescript
// src/app/api/export/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { MindMeisterClient } from '@/lib/mindmeister'
import { verifySession } from '@/lib/payment'
import { cookies } from 'next/headers'
import JSZip from 'jszip'

const ZIPPED_FORMATS = new Set(['mm', 'mind', 'xmind'])

function safeName(title: string): string {
  return title.replace(/[\\/:*?"<>|]/g, '_').replace(/\s+/g, '_') || 'untitled'
}

async function unzipFirst(buf: ArrayBuffer): Promise<ArrayBuffer> {
  try {
    const zip = await JSZip.loadAsync(buf)
    const first = Object.values(zip.files).find(f => !f.dir)
    if (first) return (await first.async('arraybuffer'))
  } catch { /* not a zip */ }
  return buf
}

export async function POST(req: NextRequest) {
  const cookieStore = await cookies()
  const sessionToken = cookieStore.get('export_session')?.value
  if (!sessionToken || !verifySession(sessionToken)) {
    return NextResponse.json({ error: 'Payment required' }, { status: 402 })
  }

  const { token, maps, format } = await req.json()
  if (!token || !maps?.length) {
    return NextResponse.json({ error: 'Missing token or maps' }, { status: 400 })
  }

  const client = new MindMeisterClient(token)
  const zip = new JSZip()

  for (const map of maps) {
    try {
      let buf = await client.exportMap(map.id, format)
      if (ZIPPED_FORMATS.has(format)) buf = await unzipFirst(buf)
      zip.file(`${safeName(map.title)}.${format}`, buf)
      // Also grab PDF alongside mm for archiving
      if (format === 'mm') {
        const pdfBuf = await client.exportMap(map.id, 'pdf')
        zip.file(`${safeName(map.title)}.pdf`, pdfBuf)
      }
    } catch (e) {
      zip.file(`${safeName(map.title)}_ERROR.txt`, String(e))
    }
    // Rate limit courtesy delay
    await new Promise(r => setTimeout(r, 500))
  }

  const zipBytes = await zip.generateAsync({ type: 'nodebuffer' })
  return new NextResponse(zipBytes, {
    headers: {
      'Content-Type': 'application/zip',
      'Content-Disposition': 'attachment; filename="my-mindmaps.zip"',
    },
  })
}
```

**Step 3: Commit**

```bash
git add src/app/api/maps/route.ts src/app/api/export/route.ts
git commit -m "feat: server-side map list and export proxy routes"
```

---

### Task 5: UI — landing page + token entry

**Files:**
- Modify: `src/app/page.tsx`
- Create: `src/components/TokenForm.tsx`

**Step 1: Landing page (page.tsx)**

Simple, direct copy. Three sections: problem statement, how it works, "Get Started" button.

```tsx
// src/app/page.tsx
import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center px-4">
      <div className="max-w-2xl text-center space-y-8">
        <h1 className="text-4xl font-bold">
          Your mind maps. <span className="text-yellow-400">Your data.</span>
        </h1>
        <p className="text-xl text-gray-300">
          MindMeister locks bulk export behind a Business plan.
          This tool uses their own public API to export all your maps
          — no upgrade required.
        </p>
        <div className="grid grid-cols-3 gap-4 text-sm text-gray-400">
          <div className="bg-gray-900 rounded p-4">
            <div className="text-2xl mb-2">🔑</div>
            <div>Paste your API token</div>
          </div>
          <div className="bg-gray-900 rounded p-4">
            <div className="text-2xl mb-2">✅</div>
            <div>Select maps to export</div>
          </div>
          <div className="bg-gray-900 rounded p-4">
            <div className="text-2xl mb-2">📦</div>
            <div>Download your zip ($5)</div>
          </div>
        </div>
        <div className="space-y-3">
          <Link
            href="/export"
            className="inline-block bg-yellow-400 text-gray-950 font-bold px-8 py-3 rounded-lg hover:bg-yellow-300 transition"
          >
            Export my maps →
          </Link>
          <p className="text-xs text-gray-500">
            Your API token is never stored. All exports happen in your session.
            <a
              href="https://github.com/gavinc/meister-export-web"
              className="underline ml-1"
            >Source on GitHub.</a>
          </p>
        </div>
      </div>
    </main>
  )
}
```

**Step 2: Commit**

```bash
git add src/app/page.tsx
git commit -m "feat: landing page"
```

---

### Task 6: UI — export page (token → map list → pay → download)

**Files:**
- Create: `src/app/export/page.tsx`
- Create: `src/components/MapSelector.tsx`

This is the main UX flow. It's a client component with three states:
1. `token-entry` — paste your token, "Load my maps"
2. `map-selection` — checkbox list of all maps, "Select all", format hint, "Export selected ($5)"
3. `downloading` — progress indicator, then auto-download

**Step 1: MapSelector component**

```tsx
// src/components/MapSelector.tsx
'use client'
import { useState } from 'react'
import type { MapInfo } from '@/lib/mindmeister'

interface Props {
  maps: MapInfo[]
  onExport: (selected: MapInfo[]) => void
  loading: boolean
}

export function MapSelector({ maps, onExport, loading }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set(maps.map(m => m.id)))

  const toggle = (id: string) =>
    setSelected(s => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n })

  const toggleAll = () =>
    setSelected(selected.size === maps.length ? new Set() : new Set(maps.map(m => m.id)))

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <span className="text-gray-400">{maps.length} maps found</span>
        <button onClick={toggleAll} className="text-sm text-yellow-400 underline">
          {selected.size === maps.length ? 'Deselect all' : 'Select all'}
        </button>
      </div>
      <ul className="space-y-1 max-h-96 overflow-y-auto">
        {maps.map(m => (
          <li
            key={m.id}
            className="flex items-center gap-3 p-2 rounded hover:bg-gray-800 cursor-pointer"
            onClick={() => toggle(m.id)}
          >
            <input
              type="checkbox"
              checked={selected.has(m.id)}
              onChange={() => toggle(m.id)}
              className="w-4 h-4 accent-yellow-400"
            />
            <span className="flex-1">{m.title}</span>
            <span className="text-xs text-gray-500">{m.modified?.slice(0, 10)}</span>
          </li>
        ))}
      </ul>
      <p className="text-sm text-gray-400">
        Exports as <strong>.mm</strong> (FreeMind) + <strong>.pdf</strong> for each map.
      </p>
      <button
        disabled={selected.size === 0 || loading}
        onClick={() => onExport(maps.filter(m => selected.has(m.id)))}
        className="w-full bg-yellow-400 text-gray-950 font-bold py-3 rounded-lg disabled:opacity-50 hover:bg-yellow-300 transition"
      >
        {loading ? 'Preparing export…' : `Export ${selected.size} maps ($5)`}
      </button>
    </div>
  )
}
```

**Step 2: Export page**

```tsx
// src/app/export/page.tsx
'use client'
import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { MapSelector } from '@/components/MapSelector'
import type { MapInfo } from '@/lib/mindmeister'

type Stage = 'token' | 'maps' | 'paying' | 'exporting' | 'done' | 'error'

export default function ExportPage() {
  const searchParams = useSearchParams()
  const stripeSessionId = searchParams.get('session_id')

  const [stage, setStage] = useState<Stage>('token')
  const [token, setToken] = useState('')
  const [maps, setMaps] = useState<MapInfo[]>([])
  const [error, setError] = useState('')

  // Came back from Stripe with a session ID — verify and proceed
  useEffect(() => {
    if (!stripeSessionId) return
    const saved = sessionStorage.getItem('mm_token')
    if (!saved) { setError('Session expired. Please start again.'); setStage('error'); return }
    setToken(saved)
    fetch('/api/verify-payment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sessionId: stripeSessionId }),
    }).then(r => r.json()).then(d => {
      if (d.ok) loadMaps(saved)
      else { setError('Payment verification failed'); setStage('error') }
    })
  }, [stripeSessionId])

  async function loadMaps(t = token) {
    setStage('maps')
    const resp = await fetch('/api/maps', { headers: { 'x-mm-token': t } })
    const data = await resp.json()
    if (!resp.ok) { setError(data.error); setStage('error'); return }
    setMaps(data.maps)
  }

  async function handleTokenSubmit() {
    if (!token.trim()) return
    sessionStorage.setItem('mm_token', token.trim())
    // Load maps first to validate token, then go to payment
    const resp = await fetch('/api/maps', { headers: { 'x-mm-token': token.trim() } })
    const data = await resp.json()
    if (!resp.ok) { setError(`Invalid token: ${data.error}`); return }
    setMaps(data.maps)
    setStage('maps')
  }

  async function handleExport(selected: MapInfo[]) {
    // Start Stripe checkout — save selection and token for after return
    sessionStorage.setItem('mm_token', token)
    sessionStorage.setItem('mm_selected', JSON.stringify(selected))
    setStage('paying')
    const resp = await fetch('/api/checkout', { method: 'POST' })
    const { url } = await resp.json()
    window.location.href = url
  }

  async function startDownload() {
    const saved = sessionStorage.getItem('mm_token')
    const selectedRaw = sessionStorage.getItem('mm_selected')
    if (!saved || !selectedRaw) { setError('Session lost'); setStage('error'); return }
    setStage('exporting')
    const resp = await fetch('/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: saved, maps: JSON.parse(selectedRaw), format: 'mm' }),
    })
    if (!resp.ok) { setError('Export failed'); setStage('error'); return }
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'my-mindmaps.zip'
    a.click()
    setStage('done')
    sessionStorage.removeItem('mm_token')
    sessionStorage.removeItem('mm_selected')
  }

  // Auto-start download once payment verified and token loaded
  useEffect(() => {
    if (stripeSessionId && token && stage === 'maps') startDownload()
  }, [stripeSessionId, token, stage])

  return (
    <main className="min-h-screen bg-gray-950 text-white flex flex-col items-center px-4 py-16">
      <div className="w-full max-w-xl space-y-8">
        <h1 className="text-3xl font-bold">Export your MindMeister maps</h1>

        {stage === 'error' && (
          <div className="bg-red-900/50 border border-red-500 rounded p-4 text-red-200">
            {error}
            <button onClick={() => setStage('token')} className="block mt-2 underline text-sm">
              Start over
            </button>
          </div>
        )}

        {stage === 'token' && (
          <div className="space-y-4">
            <p className="text-gray-400">
              Get your API token from{' '}
              <a href="https://www.mindmeister.com/api/settings" className="underline text-yellow-400" target="_blank">
                mindmeister.com/api/settings
              </a>
            </p>
            <input
              type="password"
              value={token}
              onChange={e => setToken(e.target.value)}
              placeholder="Paste your MindMeister API token"
              className="w-full bg-gray-900 border border-gray-700 rounded px-4 py-3 focus:border-yellow-400 outline-none"
              onKeyDown={e => e.key === 'Enter' && handleTokenSubmit()}
            />
            <button
              onClick={handleTokenSubmit}
              disabled={!token.trim()}
              className="w-full bg-yellow-400 text-gray-950 font-bold py-3 rounded-lg disabled:opacity-50"
            >
              Load my maps →
            </button>
            <p className="text-xs text-gray-500">Token stays in your browser only. Never sent to our servers except to proxy the MindMeister API call.</p>
          </div>
        )}

        {stage === 'maps' && !stripeSessionId && (
          <MapSelector maps={maps} onExport={handleExport} loading={false} />
        )}

        {(stage === 'paying' || stage === 'exporting') && (
          <div className="text-center space-y-4">
            <div className="text-4xl animate-spin">⚙️</div>
            <p>{stage === 'paying' ? 'Redirecting to payment…' : `Exporting ${maps.length} maps…`}</p>
          </div>
        )}

        {stage === 'done' && (
          <div className="text-center space-y-4">
            <div className="text-5xl">✅</div>
            <p className="text-xl">Your maps have been downloaded!</p>
            <button onClick={() => { setStage('token'); setToken('') }} className="underline text-sm text-gray-400">
              Export again
            </button>
          </div>
        )}
      </div>
    </main>
  )
}
```

**Step 3: Commit**

```bash
git add src/components/MapSelector.tsx src/app/export/page.tsx
git commit -m "feat: export UI — token entry, map selection, Stripe flow, download"
```

---

### Task 7: Vercel deployment

**Step 1: Push to gavinc GitHub**

```bash
eval "$(ssh-agent -s)" && ssh-add /home/heavygee/.ssh/id_rsa_gavinc
git remote add origin git@github-gc:gavinc/meister-export-web.git
gh-ll repo create gavinc/meister-export-web \
  --public \
  --description "Export all your MindMeister maps without a Business plan — web interface" \
  --push --source .
```

**Step 2: Deploy to Vercel (preview first)**

Use the `vercel:deploy` skill or run:
```bash
npx vercel --yes
```

**Step 3: Set environment variables on Vercel**

```bash
npx vercel env add STRIPE_SECRET_KEY
npx vercel env add STRIPE_PUBLISHABLE_KEY
npx vercel env add STRIPE_WEBHOOK_SECRET
npx vercel env add STRIPE_PRICE_ID
npx vercel env add SESSION_SECRET
npx vercel env add NEXT_PUBLIC_APP_URL
```

**Step 4: Create Stripe product**

In Stripe dashboard:
1. Products → Create product: "MindMeister Map Export"
2. Price: $5.00 one-time
3. Copy the `price_xxx` ID → set as `STRIPE_PRICE_ID`

**Step 5: Test full flow**
1. Open preview URL
2. Paste real API token → verify maps load
3. Select a few maps → click export
4. Use Stripe test card `4242 4242 4242 4242`
5. Verify zip downloads with correct files

**Step 6: Deploy to production**

```bash
npx vercel --prod
```

**Step 7: Set NEXT_PUBLIC_APP_URL to production URL**

---

## Summary

| Endpoint | Purpose |
|---|---|
| `GET /api/maps` | List user maps (proxied, token in header) |
| `POST /api/checkout` | Create Stripe checkout session |
| `POST /api/verify-payment` | Verify payment, set signed cookie |
| `POST /api/export` | Bulk export + zip download (requires valid cookie) |

**Payment flow:** token entry → load maps → select → Stripe Checkout → return to `/export?session_id=xxx` → verify payment → auto-download zip → clear session.

**Never stored:** API token (sessionStorage only, cleared after download), selected maps (sessionStorage), payment method details (Stripe handles all of that).
