import fs from 'node:fs/promises'
import path from 'node:path'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import ffmpegPath from 'ffmpeg-static'
import sharp from 'sharp'

const exec = promisify(execFile)
const root = process.cwd()
const source = process.argv[2] || 'https://hebbkx1anhila5yf.public.blob.vercel-storage.com/sat-zoom-in%2B%28online-video-cutter.com%29-ZleVQXDDkGCFmmn01T2gJuDad5AFCt.webm'
const outRoot = path.join(root, 'public', 'hero-atlas')
const tempRoot = path.join(root, '.hero-frames')
const fps = 24
const atlasSize = 24
const columns = 6
const rows = 4
const configs = [
  { name: 'desktop', width: 960, quality: 86 },
  { name: 'mobile', width: 640, quality: 82 },
]

await fs.mkdir(outRoot, { recursive: true })
await fs.mkdir(tempRoot, { recursive: true })
const sourceFile = path.join(tempRoot, 'source.webm')
if (!source.startsWith('http')) await fs.copyFile(source, sourceFile)
else {
  const response = await fetch(source)
  if (!response.ok) throw new Error(`Could not download source: ${response.status}`)
  await fs.writeFile(sourceFile, Buffer.from(await response.arrayBuffer()))
}
let probe = ''
try {
  const probeResult = await exec(ffmpegPath, ['-i', sourceFile, '-hide_banner'])
  probe = `${probeResult.stdout}\n${probeResult.stderr}`
} catch (error) {
  probe = `${error.stdout || ''}\n${error.stderr || ''}`
}
const durationMatch = probe.match(/Duration: (\d+):(\d+):(\d+\.\d+)/)
const duration = durationMatch ? Number(durationMatch[1]) * 3600 + Number(durationMatch[2]) * 60 + Number(durationMatch[3]) : 9
const frameCount = Math.ceil(duration * fps)

for (const config of configs) {
  const frameDir = path.join(tempRoot, config.name)
  await fs.rm(frameDir, { recursive: true, force: true })
  await fs.mkdir(frameDir, { recursive: true })
  await exec(ffmpegPath, ['-y', '-i', sourceFile, '-vf', `fps=${fps},scale=${config.width}:-2:flags=lanczos`, '-frames:v', String(frameCount), path.join(frameDir, 'frame-%04d.png')])
  console.log(config.name, 'extracted', (await fs.readdir(frameDir)).length, 'frames')
  const first = sharp(path.join(frameDir, 'frame-0001.png'))
  const meta = await first.metadata()
  const frameWidth = meta.width
  const frameHeight = meta.height
  const atlasWidth = frameWidth * columns
  const atlasHeight = frameHeight * rows
  let generated = 0
  for (let start = 0; start < frameCount; start += atlasSize) {
    const composites = []
    for (let local = 0; local < atlasSize; local++) {
      const file = path.join(frameDir, `frame-${String(start + local + 1).padStart(4, '0')}.png`)
      try {
        await fs.access(file)
        composites.push({ input: file, left: (local % columns) * frameWidth, top: Math.floor(local / columns) * frameHeight })
        generated += 1
      } catch {}
    }
    if (!composites.length) continue
    await sharp({ create: { width: atlasWidth, height: atlasHeight, channels: 3, background: '#000' } })
      .composite(composites)
      .webp({ quality: config.quality, effort: 4 })
      .toFile(path.join(outRoot, `${config.name}-${String(start / atlasSize).padStart(2, '0')}.webp`))
  }
  await fs.writeFile(path.join(outRoot, `${config.name}.json`), JSON.stringify({ frameCount, fps, columns, rows, frameWidth, frameHeight, atlasCount: Math.ceil(frameCount / atlasSize), atlasSize }, null, 2))
  console.log(`${config.name}: ${generated} frames, ${frameWidth}x${frameHeight}, ${Math.ceil(frameCount / atlasSize)} atlases`)
}
// Temporary extracted frames are removed after successful atlas generation in CI.
