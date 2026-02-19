const API = 'http://localhost:8000'


let selectedFiles = []
let currentResult = null
let startTime = null

const zone = document.getElementById('upload-zone')
const fileInput = document.getElementById('file-input')
const fileList = document.getElementById('file-list')
const processBtnWrap = document.getElementById('process-btn-wrap')
const processBtn = document.getElementById('process-btn')

zone.addEventListener('click', e => {
  if (e.target.closest('.btn')) return
  fileInput.click()
})

zone.addEventListener('dragover', e => {
  e.preventDefault()
  zone.classList.add('drag-over')
})

zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'))

zone.addEventListener('drop', e => {
  e.preventDefault()
  zone.classList.remove('drag-over')
  const files = [...e.dataTransfer.files].filter(f =>
    f.type === 'application/pdf' || f.type.startsWith('image/')
  )
  if (files.length) addFiles(files)
})

fileInput.addEventListener('change', e => {
  if (e.target.files.length) addFiles([...e.target.files])
  fileInput.value = ''
})

function addFiles(files) {
  selectedFiles = [...selectedFiles, ...files]
  renderFileList()
}

function renderFileList() {
  fileList.innerHTML = ''
  if (!selectedFiles.length) {
    processBtnWrap.style.display = 'none'
    return
  }
  processBtnWrap.style.display = 'block'

  selectedFiles.forEach((file, i) => {
    const item = document.createElement('div')
    item.className = 'file-item'
    item.innerHTML = `
      <div class="file-item-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
      </div>
      <div class="file-item-info">
        <div class="file-item-name">${file.name}</div>
        <div class="file-item-size">${formatSize(file.size)}</div>
      </div>
      <button class="file-item-remove" onclick="removeFile(${i})">
        <svg viewBox="0 0 24 24">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    `
    fileList.appendChild(item)
  })
}

function removeFile(index) {
  selectedFiles.splice(index, 1)
  renderFileList()
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function showPanel(name) {
  document.getElementById('panel-empty').style.display = 'none'
  document.getElementById('panel-loading').style.display = 'none'
  document.getElementById('panel-results').style.display = 'none'

  if (name === 'empty') document.getElementById('panel-empty').style.display = 'flex'
  if (name === 'loading') document.getElementById('panel-loading').style.display = 'block'
  if (name === 'results') document.getElementById('panel-results').style.display = 'block'
}

async function processFiles() {
  if (!selectedFiles.length) return

  processBtn.disabled = true
  processBtn.innerHTML = `
    <svg viewBox="0 0 24 24" style="animation:spin .8s linear infinite">
      <line x1="12" y1="2" x2="12" y2="6"/>
      <line x1="12" y1="18" x2="12" y2="22"/>
      <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
      <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
      <line x1="2" y1="12" x2="6" y2="12"/>
      <line x1="18" y1="12" x2="22" y2="12"/>
      <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/>
      <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
    </svg>
    Processing...
  `

  showPanel('loading')
  startTime = Date.now()

  try {
    const formData = new FormData()

    // ✅ FIX: append multiple files correctly
    selectedFiles.forEach(file => {
      formData.append('files', file)
    })

    const res = await fetch(`${API}/ocr/process`, {
      method: 'POST',
      body: formData
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }

    const apiResponse = await res.json()

    if (!apiResponse.results || !apiResponse.results.length) {
      throw new Error("No OCR results returned from server")
    }

    // ✅ extract first document OCR result
    const firstDoc = apiResponse.results[0].ocr_result

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1)

    currentResult = firstDoc

    renderResults(firstDoc, parseFloat(elapsed))
    showPanel('results')

  } catch (err) {
    showToast('Error: ' + err.message)
    showPanel('empty')
  } finally {
    processBtn.disabled = false
    processBtn.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="5 3 19 12 5 21 5 3"/>
      </svg>
      Process Document
    `
  }
}

function renderResults(data, elapsed) {
  const conf = parseFloat(data.average_confidence || data.confidence || 0)
  const pages = data.page_count || 1
  const words = data.total_words || 0
  const chars = data.total_characters || 0

  document.getElementById('res-pages').textContent = pages
  document.getElementById('res-words').textContent = words.toLocaleString()
  document.getElementById('res-chars').textContent = chars.toLocaleString()

  const confEl = document.getElementById('res-conf')
  confEl.textContent = conf.toFixed(1) + '%'
  confEl.className = 'meta-value ' + (conf >= 90 ? 'green' : conf >= 70 ? 'yellow' : 'red')

  const badge = document.getElementById('res-doc-badge')
  if (data.is_scanned !== undefined) {
    badge.innerHTML = data.is_scanned
      ? `<div class="doc-type-badge scanned">Scanned document — OCR applied</div>`
      : `<div class="doc-type-badge text">Text-based PDF — Direct extraction</div>`
  } else {
    badge.innerHTML = ''
  }

  document.getElementById('res-text').textContent = data.text || 'No text extracted'

  updateStats(pages, conf, elapsed)
  renderPages(data.pages)
}

function renderPages(pages) {
  const section = document.getElementById('pages-section')
  const list = document.getElementById('pages-list')
  list.innerHTML = ''

  if (!pages || pages.length <= 1) {
    section.style.display = 'none'
    return
  }

  section.style.display = 'block'

  pages.forEach((page, i) => {
    const num = page.page_number || i + 1
    const conf = parseFloat(page.confidence || 0)
    const words = page.word_count || 0
    const confClass = conf >= 90 ? 'high' : conf >= 70 ? 'mid' : 'low'
    const id = `page-body-${i}`
    const chevId = `chev-${i}`

    const item = document.createElement('div')
    item.className = 'page-item'
    item.innerHTML = `
      <div class="page-header" onclick="togglePage('${id}','${chevId}')">
        <div class="page-header-left">
          <span class="page-num">Page ${num}</span>
          <span class="confidence-tag ${confClass}">${conf.toFixed(1)}%</span>
        </div>
        <div class="page-header-right">
          <span class="page-words">${words} words</span>
          <svg id="${chevId}" class="chevron" viewBox="0 0 24 24">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </div>
      <div class="page-body" id="${id}">
        <div class="page-text">${escapeHtml(page.text || 'No text')}</div>
      </div>
    `
    list.appendChild(item)
  })
}

function togglePage(bodyId, chevId) {
  const body = document.getElementById(bodyId)
  const chev = document.getElementById(chevId)
  const open = body.classList.toggle('open')
  chev.classList.toggle('open', open)
}

function updateStats(pages, conf, elapsed) {
  document.getElementById('stat-processed').textContent = pages
  document.getElementById('stat-success').textContent = '100%'
  document.getElementById('stat-confidence').textContent = conf.toFixed(1) + '%'
  document.getElementById('stat-time').textContent = elapsed + 's'
}

function copyText() {
  if (!currentResult) return
  navigator.clipboard.writeText(currentResult.text || '')
    .then(() => showToast('Copied to clipboard!'))
}

function downloadText() {
  if (!currentResult) return
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([currentResult.text || ''], { type: 'text/plain' }))
  a.download = 'ocr-result.txt'
  a.click()
  showToast('Download started!')
}

function showToast(msg) {
  const toast = document.getElementById('toast')
  document.getElementById('toast-msg').textContent = msg
  toast.classList.add('show')
  setTimeout(() => toast.classList.remove('show'), 2500)
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
}


