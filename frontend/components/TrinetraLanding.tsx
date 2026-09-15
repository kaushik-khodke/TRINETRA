'use client'

import { useEffect, useRef, useState } from 'react'
import { Radar } from 'lucide-react'

const dummyImage = 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=1200&q=80'

const capabilities = [
  ['01', 'Sense', 'Capture information from available Earth-observation data.'],
  ['02', 'Understand', 'Extract visual, spectral, spatial, temporal, and radiometric information.'],
  ['03', 'Analyze', 'Apply the specialized intelligence models required for the task.'],
  ['04', 'Validate', 'Compare model evidence and confidence, including quantum validation.'],
  ['05', 'Explain', 'Turn the technical result into an understandable answer.'],
]

const models = [
  ['Land-Cover Intelligence', 'BigEarthNetAdaptedResNet', 'Classify urban fabric, industry, forests, agriculture, and water bodies.', '91%'],
  ['Ask Questions About the Image', 'RSVqaFusionNetwork', 'Combine imagery with natural-language questions about a scene.', 'HIGH'],
  ['Find What You Mean', 'RSGroundingDetector', 'Locate the region that matches a natural-language reference.', 'BOUND'],
  ['Detect What Changed', 'SiameseChangeDiffNet', 'Compare observations across time to identify expansion, loss, or stability.', '84%'],
]

function ScrollCinema() {
  const sectionRef = useRef<HTMLElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const eyebrowRef = useRef<HTMLParagraphElement>(null)
  const phaseRef = useRef<HTMLHeadingElement>(null)
  const scrollFillRef = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const section = sectionRef.current
    if (!canvas || !section) return

    let targetFrame = 0
    let renderedFrame = -1
    let renderQueued = false
    let cancelled = false
    const atlasCache = new Map<number, HTMLImageElement>()
    const atlasCount = 10
    const atlasSize = 24
    const columns = 6
    const rows = 4
    const frameCount = 221
    const frameWidth = window.matchMedia('(max-width: 700px)').matches ? 640 : 960
    const frameHeight = window.matchMedia('(max-width: 700px)').matches ? 356 : 534
    let activeAtlas = -1

    const resizeCanvas = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const width = Math.round(window.innerWidth * dpr)
      const height = Math.round(window.innerHeight * dpr)
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width
        canvas.height = height
      }
    }

    const drawAtlasFrame = (atlas: HTMLImageElement, index: number) => {
      if (index === renderedFrame) return
      const context = canvas.getContext('2d')
      if (!context) return
      const local = index % atlasSize
      const sourceX = (local % columns) * frameWidth
      const sourceY = Math.floor(local / columns) * frameHeight
      resizeCanvas()
      const scale = Math.max(canvas.width / frameWidth, canvas.height / frameHeight)
      const drawWidth = frameWidth * scale
      const drawHeight = frameHeight * scale
      context.drawImage(
        atlas,
        sourceX,
        sourceY,
        frameWidth,
        frameHeight,
        (canvas.width - drawWidth) / 2,
        (canvas.height - drawHeight) / 2,
        drawWidth,
        drawHeight
      )
      renderedFrame = index
    }

    const loadAtlas = (index: number) => {
      if (index < 0 || index >= atlasCount || atlasCache.has(index)) return atlasCache.get(index)
      const image = new Image()
      image.decoding = 'async'
      atlasCache.set(index, image)
      image.src = `/hero-atlas/${frameWidth === 640 ? 'mobile' : 'desktop'}-${String(index).padStart(2, '0')}.webp`
      image.onload = () => {
        if (!cancelled && (activeAtlas === index || renderedFrame < 0)) requestRender()
      }
      return image
    }

    const renderLatest = () => {
      renderQueued = false
      if (cancelled) return
      const atlasIndex = Math.floor(targetFrame / atlasSize)
      const atlas = atlasCache.get(atlasIndex) || loadAtlas(atlasIndex)
      if (atlas && atlas.complete && atlas.naturalWidth) {
        activeAtlas = atlasIndex
        drawAtlasFrame(atlas, targetFrame)
      }
    }

    const requestRender = () => {
      if (renderQueued) return
      renderQueued = true
      requestAnimationFrame(renderLatest)
    }

    const updateScroll = () => {
      const range = Math.max(1, section.offsetHeight - window.innerHeight)
      const progress = Math.min(1, Math.max(0, -section.getBoundingClientRect().top / range))
      targetFrame = Math.min(frameCount - 1, Math.round(progress * (frameCount - 1)))
      const atlasIndex = Math.floor(targetFrame / atlasSize)
      loadAtlas(atlasIndex)
      loadAtlas(atlasIndex - 1)
      loadAtlas(atlasIndex + 1)
      if (eyebrowRef.current) {
        eyebrowRef.current.textContent = `EARTH OBSERVATION / ${String(Math.round(progress * 100)).padStart(2, '0')}%`
      }
      if (scrollFillRef.current) {
        scrollFillRef.current.style.height = `${progress * 100}%`
      }
      if (phaseRef.current) {
        phaseRef.current.textContent =
          progress < 0.2
            ? 'THE EARTH IS FULL OF SIGNALS.'
            : progress < 0.46
            ? 'EVERY REGION TELLS A DIFFERENT STORY.'
            : progress < 0.7
            ? 'SEEING IT IS ONLY THE BEGINNING.'
            : progress < 0.88
            ? 'UNDERSTAND IT.'
            : 'MEET TRINETRA'
      }
      requestRender()
    }

    const preloadAtlases = () => {
      loadAtlas(0)
      loadAtlas(1)
      loadAtlas(2)
    }

    window.addEventListener('scroll', updateScroll, { passive: true })
    window.addEventListener('resize', resizeCanvas)
    resizeCanvas()
    updateScroll()
    preloadAtlases()

    return () => {
      cancelled = true
      window.removeEventListener('scroll', updateScroll)
      window.removeEventListener('resize', resizeCanvas)
      atlasCache.clear()
    }
  }, [])

  return (
    <section ref={sectionRef} className="cinema" aria-label="Scroll-driven satellite introduction">
      <div className="cinema-sticky">
        <canvas
          ref={canvasRef}
          className="cinema-video cinema-canvas"
          aria-label="Satellite zoom into Earth"
          role="img"
        />
        <div className="cinema-scrim" />
        <div className="grid-overlay" />
        <div className="cinema-top">
          <span>TRINETRA / 001</span>
          <span>SCROLL TO EXPLORE</span>
        </div>
        <div className="cinema-copy">
          <p ref={eyebrowRef} className="eyebrow">
            EARTH OBSERVATION / 00%
          </p>
          <h1 ref={phaseRef}>THE EARTH IS FULL OF SIGNALS.</h1>
          <p>Multimodal Earth-observation intelligence, built to see beyond the surface.</p>
        </div>
        <div className="scroll-line">
          <span ref={scrollFillRef} />
        </div>
      </div>
    </section>
  )
}

function Nav({ navigate }: { navigate: (path: string) => void }) {
  return (
    <header className="site-nav">
      <a
        href="#top"
        className="brand"
        onClick={(e) => {
          e.preventDefault()
          window.scrollTo({ top: 0, behavior: 'smooth' })
        }}
      >
        <img
          src="/trinetra-logo1.webp"
          alt="TRINETRA Logo"
          style={{ width: 24, height: 24, borderRadius: 5, objectFit: 'contain' }}
        />
        TRI<span>•</span>NETRA
      </a>
      <nav>
        <a href="#intelligence">Intelligence</a>
        <a href="#sensors">Sensors</a>
        <a href="#models">Models</a>
        <button
          onClick={() => navigate('/analysis')}
          style={{
            background: 'none',
            border: 'none',
            color: 'inherit',
            font: 'inherit',
            cursor: 'pointer',
            textTransform: 'uppercase',
            letterSpacing: '0.12em',
            padding: 0,
          }}
        >
          Workspace
        </button>
      </nav>
      <button onClick={() => navigate('/analysis')} className="nav-cta">
        Start analysis <span>↗</span>
      </button>
    </header>
  )
}

export default function TrinetraLanding({ navigate }: { navigate: (path: string) => void }) {
  const [activeCapability, setActiveCapability] = useState(0)
  const [capabilityProgress, setCapabilityProgress] = useState(0)

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const section = document.querySelector<HTMLElement>('.idea-section')
    if (prefersReducedMotion || !section) return

    let frame = 0
    let startedAt = performance.now()
    let visible = true
    const duration = 4200
    const tick = (now: number) => {
      if (visible && !document.hidden) {
        const elapsed = now - startedAt
        const progress = Math.min(1, elapsed / duration)
        setCapabilityProgress(progress)
        if (progress >= 1) {
          setActiveCapability((current) => (current + 1) % capabilities.length)
          setCapabilityProgress(0)
          startedAt = now
        }
      }
      frame = requestAnimationFrame(tick)
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        visible = entry.isIntersecting
        if (visible) startedAt = performance.now()
      },
      { threshold: 0.2 }
    )
    const onVisibilityChange = () => {
      if (!document.hidden) startedAt = performance.now() - capabilityProgress * duration
    }
    observer.observe(section)
    document.addEventListener('visibilitychange', onVisibilityChange)
    frame = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }
  }, [capabilityProgress])

  useEffect(() => {
    const sensorSection = document.querySelector<HTMLElement>('.sensor-section')
    const sensorList = sensorSection?.querySelector<HTMLElement>('.sensor-grid')
    const sensorCards = Array.from(sensorSection?.querySelectorAll<HTMLElement>('.sensor-card') ?? [])
    const sensorData = [
      ['OPTICAL', 'Spatial & Visual Information', 'Understand visible structures, land cover, objects, patterns, and scene composition.', 'SPATIAL · VISIBLE SPECTRUM · OPTICAL'],
      ['MULTISPECTRAL', 'Spectral & Vegetation Information', 'Use additional spectral bands to derive richer surface characteristics and vegetation-related signals.', 'MULTISPECTRAL · NIR · SPECTRAL'],
      ['HYPERSPECTRAL', 'Fine-Grained Spectral Information', 'Analyze detailed spectral signatures across many bands where spectral characteristics matter.', 'HIGH-DIMENSIONAL · SPECTRAL SIGNATURE · HYPERSPECTRAL'],
      ['RADAR', 'Radar-Based Information', 'Use microwave backscatter to reveal structural and surface information that optical imagery alone may miss.', 'SAR · BACKSCATTER · RADAR'],
      ['TIME', 'Change Through Time', 'Compare observations across dates to identify what has changed, expanded, decreased, or remained stable.', 'MULTI-TEMPORAL · CHANGE · TIME SERIES'],
    ]
    const activateSensor = (index: number) => {
      const data = sensorData[index]
      if (!sensorList || !data) return
      sensorList.dataset.active = String(index)
      sensorList.dataset.label = data[0]
      sensorList.dataset.title = data[1]
      sensorList.dataset.description = data[2]
      sensorList.dataset.meta = data[3]
      sensorCards.forEach((card, cardIndex) => {
        card.classList.toggle('is-active', cardIndex === index)
        card.setAttribute('aria-selected', String(cardIndex === index))
      })
    }
    sensorCards.forEach((card, index) => {
      card.setAttribute('role', 'tab')
      card.tabIndex = 0
      card.addEventListener('mouseenter', () => activateSensor(index))
      card.addEventListener('focus', () => activateSensor(index))
      card.addEventListener('click', () => activateSensor(index))
      card.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          activateSensor(index)
        }
      })
    })

    const sensorImages = [
      '/sensor-rgb-optical.jpeg',
      '/sensor-multispectral-nir.webp',
      '/sensor-hyperspectral.jpeg',
      '/sensor-sar.jpg',
      '/sensor-multi-temporal.webp',
    ]
    const sensorImage = sensorSection?.querySelector<HTMLElement>('.sensor-grid')
    const imageProgress = document.createElement('span')
    imageProgress.className = 'sensor-image-progress'
    imageProgress.innerHTML = '<span></span>'
    sensorImage?.appendChild(imageProgress)
    const sensorProgressBar = imageProgress.querySelector<HTMLElement>('span')
    let sensorFrame = 0
    let sensorStartedAt = performance.now()
    let sensorIndex = 0
    const sensorDuration = 4200

    const updateSensorVisual = (index: number, progress = 0) => {
      activateSensor(index)
      sensorIndex = index
      sensorStartedAt = performance.now() - progress * sensorDuration
      if (sensorImage) sensorImage.style.setProperty('--sensor-image', `url(${sensorImages[index]})`)
      if (sensorProgressBar) sensorProgressBar.style.width = `${progress * 100}%`
    }

    const tickSensors = (now: number) => {
      if (!document.hidden && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        const progress = Math.min(1, (now - sensorStartedAt) / sensorDuration)
        if (sensorProgressBar) sensorProgressBar.style.width = `${progress * 100}%`
        if (progress >= 1) updateSensorVisual((sensorIndex + 1) % sensorCards.length)
      }
      sensorFrame = requestAnimationFrame(tickSensors)
    }

    sensorCards.forEach((card, index) => {
      const activate = () => updateSensorVisual(index)
      card.addEventListener('mouseenter', activate)
      card.addEventListener('focus', activate)
    })
    updateSensorVisual(0)
    sensorFrame = requestAnimationFrame(tickSensors)

    const paragraphTargets = Array.from(
      document.querySelectorAll<HTMLElement>(
        '.section p:not(.lede):not(.step p), .hero-intro p, .fusion-copy p, .final-section p, .cinema-copy p:not(.eyebrow)'
      )
    )
    const paragraphWords = new Map<HTMLElement, HTMLSpanElement[]>()

    paragraphTargets.forEach((paragraph) => {
      const words: HTMLSpanElement[] = []
      const walker = document.createTreeWalker(paragraph, NodeFilter.SHOW_TEXT)
      const textNodes: Text[] = []
      while (walker.nextNode()) textNodes.push(walker.currentNode as Text)
      textNodes.forEach((node) => {
        const fragment = document.createDocumentFragment()
        node.textContent?.split(/(\s+)/).forEach((part) => {
          if (/\s+/.test(part)) fragment.appendChild(document.createTextNode(part))
          else if (part) {
            const span = document.createElement('span')
            span.className = 'scroll-word'
            span.textContent = part
            fragment.appendChild(span)
            words.push(span)
          }
        })
        node.parentNode?.replaceChild(fragment, node)
      })
      paragraphWords.set(paragraph, words)
    })

    let progressFrame = 0
    const updateWordProgress = () => {
      if (progressFrame) return
      progressFrame = window.requestAnimationFrame(() => {
        progressFrame = 0
        const viewportHeight = window.innerHeight
        const scrollTop = window.scrollY
        paragraphWords.forEach((words, paragraph) => {
          const rect = paragraph.getBoundingClientRect()
          const documentTop = rect.top + scrollTop
          const progressRange = Math.max(1, paragraph.offsetHeight + viewportHeight * 0.22)
          const paragraphProgress = Math.min(1, Math.max(0, (scrollTop + viewportHeight * 0.78 - documentTop) / progressRange))
          const isLightSection = paragraph.closest('.idea-section') !== null
          words.forEach((word, index) => {
            const wordStart = index / Math.max(1, words.length)
            const activation = Math.min(1, Math.max(0, (paragraphProgress - wordStart) * words.length * 1.8))
            word.style.setProperty('--word-progress', activation.toFixed(3))
            if (isLightSection) word.style.setProperty('color', '#1f201c', 'important')
          })
        })
      })
    }

    const targets = document.querySelectorAll<HTMLElement>(
      '.section-kicker, .section h2, .section p:not(.step p), .cinema-copy p, .hero-intro, .capability-line, .image-panel, .sensor-card, .model-row, .fusion-copy, .evidence-card, footer > *'
    )
    targets.forEach((target, index) => {
      target.classList.add('reveal')
      target.style.setProperty('--reveal-delay', `${Math.min(index % 5, 4) * 70}ms`)
    })
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible')
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.14 }
    )
    targets.forEach((target) => observer.observe(target))
    window.addEventListener('scroll', updateWordProgress, { passive: true })
    window.addEventListener('resize', updateWordProgress)
    updateWordProgress()

    return () => {
      cancelAnimationFrame(sensorFrame)
      imageProgress.remove()
      observer.disconnect()
      window.removeEventListener('scroll', updateWordProgress)
      window.removeEventListener('resize', updateWordProgress)
    }
  }, [])

  return (
    <main id="top" className="trinetra-landing-root">
      <Nav navigate={navigate} />
      <ScrollCinema />

      {/* Hero Section */}
      <section className="section hero-section">
        <div className="section-kicker">
          AI-POWERED EARTH OBSERVATION <span>01 / 08</span>
        </div>
        <div className="hero-grid">
          <div>
            <h2>
              See Earth.
              <br />
              <em>Understand</em> what&apos;s happening.
            </h2>
          </div>
          <div className="hero-intro">
            <p>
              TRINETRA turns satellite and remote-sensing data into intelligent, explainable insights using specialized
              vision models, multimodal fusion, quantum validation, and local AI reasoning.
            </p>
            <button className="button" onClick={() => navigate('/analysis')}>
              Start analysis <span>↗</span>
            </button>
            <a className="text-link" href="#intelligence">
              Explore how it works <span>↓</span>
            </a>
          </div>
        </div>
        <div className="capability-line">
          Land Cover <i>·</i> Change Detection <i>·</i> Visual Q&amp;A <i>·</i> Region Grounding <i>·</i> Optical + SAR{' '}
          <i>·</i> QML Validation
        </div>
      </section>

      {/* Problem Section */}
      <section className="section problem-section">
        <div className="section-kicker">THE SIGNAL / 02</div>
        <div className="split-heading">
          <h2>
            More data.
            <br />
            <em>More to understand.</em>
          </h2>
          <p>
            Satellite imagery can reveal vegetation, buildings, water, terrain, materials, environmental conditions, and
            changes across time. But understanding all of that information often requires different sensors, models, and
            analytical workflows.
            <br />
            <br />
            <strong>TRINETRA brings these perspectives together in one adaptive analysis pipeline.</strong>
          </p>
        </div>
        <div className="image-panel">
          <img src={dummyImage} alt="Earth viewed from orbit" />
          <span>RGB / NIR / SAR / TEMPORAL</span>
        </div>
      </section>

      {/* Intelligence Section */}
      <section className="section idea-section" id="intelligence">
        <div className="section-kicker">THE CORE IDEA / 03</div>
        <h2>
          One Earth.
          <br />
          <em>Multiple perspectives.</em>
        </h2>
        <p className="lede">
          TRINETRA determines what you are asking, identifies the available data, selects the right analytical pathway,
          and combines the resulting evidence.
        </p>
        <div className="steps">
          {capabilities.map(([number, title, text], index) => (
            <article
              className={`step ${activeCapability === index ? 'is-active' : ''}`}
              key={number}
              tabIndex={0}
              aria-current={activeCapability === index ? 'step' : undefined}
              onMouseEnter={() => setActiveCapability(index)}
              onFocus={() => setActiveCapability(index)}
              onClick={() => setActiveCapability(index)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault()
                  setActiveCapability(index)
                }
              }}
            >
              <span>{number}</span>
              <h3>{title}</h3>
              <p>{text}</p>
              <span className="step-progress" aria-hidden="true">
                <span
                  style={{
                    width: activeCapability === index ? `${capabilityProgress * 100}%` : '0%',
                  }}
                />
              </span>
            </article>
          ))}
        </div>
        <p className="closing-line">
          From pixels to perception.
          <br />
          <em>From perception to understanding.</em>
        </p>
      </section>

      {/* Sensor Section */}
      <section className="section sensor-section" id="sensors">
        <div className="section-kicker">THE DATA / 04</div>
        <div className="split-heading">
          <h2>
            Different sensors
            <br />
            <em>see different truths.</em>
          </h2>
          <p>
            The intelligence pipeline adapts to the data available for the task. No single perspective tells the whole
            story.
          </p>
        </div>
        <div className="sensor-grid">
          {['RGB / Optical', 'Multispectral / NIR', 'Hyperspectral', 'SAR', 'Multi-Temporal Imagery'].map((title, i) => (
            <article key={title} className="sensor-card">
              <span>0{i + 1}</span>
              <h3>{title}</h3>
              <p>
                {
                  [
                    'Spatial & visual information',
                    'Spectral & vegetation information',
                    'Fine-grained spectral information',
                    'Radar-based information',
                    'Change through time',
                  ][i]
                }
              </p>
            </article>
          ))}
        </div>
      </section>

      {/* Specialized Models Section */}
      <section className="section models-section" id="models">
        <div className="section-kicker">SPECIALIZED AI / 05</div>
        <h2>
          One question.
          <br />
          <em>The right intelligence.</em>
        </h2>
        <p className="lede">
          Instead of forcing every question through the same model, TRINETRA chooses the intelligence that fits the
          evidence.
        </p>
        <div className="model-list">
          {models.map(([title, model, text, metric], index) => (
            <article className="model-row" key={model}>
              <span className="model-index">0{index + 1}</span>
              <div>
                <h3>{title}</h3>
                <code>{model}</code>
              </div>
              <p>{text}</p>
              <strong>{metric}</strong>
            </article>
          ))}
        </div>
      </section>

      {/* Evidence Fusion Section */}
      <section className="section fusion-section">
        <div className="fusion-copy">
          <div className="section-kicker">EVIDENCE FUSION / 06</div>
          <h2>
            TRINETRA doesn&apos;t just predict.
            <br />
            <em>It compares evidence.</em>
          </h2>
          <p>
            A single model can provide an answer. TRINETRA evaluates multiple sources of evidence before presenting the
            result.
          </p>
          <button
            className="text-link"
            onClick={() => navigate('/analysis')}
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
          >
            Launch workspace <span>↗</span>
          </button>
        </div>
        <div className="evidence-card">
          <div className="evidence-head">
            <span>ANALYSIS / REGION 44.912</span>
            <b>● LIVE</b>
          </div>
          {[
            ['Land cover', 'Vegetation', '91%'],
            ['Visual Q&A', 'Vegetation present', 'HIGH'],
            ['Change', 'No significant change', '84%'],
            ['QML validation', 'Independent agreement', 'YES'],
          ].map(([a, b, c]) => (
            <div className="evidence-row" key={a}>
              <span>{a}</span>
              <strong>{b}</strong>
              <b>{c}</b>
            </div>
          ))}
          <div className="result">
            <span>FINAL RESULT</span>
            <strong>VEGETATION</strong>
            <small>Confidence: High · Optical + Spectral + Model Agreement</small>
          </div>
        </div>
      </section>

      {/* Ask TRINETRA Section */}
      <section className="section ask-section">
        <div className="section-kicker">ASK TRINETRA / 07</div>
        <h2>
          You don&apos;t need to know
          <br />
          <em>which model to use.</em>
        </h2>
        <p className="lede">Just tell TRINETRA what you want to know.</p>
        <div className="prompt-cloud">
          {[
            'What is present in this region?',
            'Find the buildings in this image.',
            'What changed between these images?',
            'Is vegetation increasing here?',
            'Compare optical and radar evidence.',
          ].map((prompt) => (
            <button
              key={prompt}
              onClick={() => navigate(`/analysis?query=${encodeURIComponent(prompt)}`)}
              title="Open query in Workspace"
            >
              {prompt} <span>↗</span>
            </button>
          ))}
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="section final-section" id="start">
        <div className="section-kicker">TRINETRA / 08</div>
        <h2>
          Look beyond
          <br />
          <em>the image.</em>
        </h2>
        <p>
          Upload your Earth-observation data. Ask your question. Let TRINETRA uncover the evidence behind the scene.
        </p>
        <button className="button light" onClick={() => navigate('/analysis')}>
          Start analysis <span>↗</span>
        </button>
      </section>

      {/* Footer */}
      <footer>
        <div className="brand">
          <img
            src="/trinetra-logo1.webp"
            alt="TRINETRA"
            style={{ width: 22, height: 22, marginRight: 8, verticalAlign: 'middle', borderRadius: 4 }}
          />
          TRI<span>•</span>NETRA
        </div>
        <p>
          Modular Earth-Observation Intelligence
          <br />
          Analyze · Compare · Understand
        </p>
        <div>Computer Vision · Remote Sensing · Multimodal AI · QML · Local LLMs</div>
      </footer>
    </main>
  )
}
