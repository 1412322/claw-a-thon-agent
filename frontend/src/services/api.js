// Use relative path for production (same-origin), localhost for dev
const BASE_URL = import.meta.env.DEV ? 'http://localhost:8000' : ''

export async function fetchProjects() {
  const res = await fetch(`${BASE_URL}/api/v1/projects/`)
  if (!res.ok) throw new Error('Failed to fetch projects')
  return res.json()
}

export async function uploadDocument(projectId, projectName, file) {
  const formData = new FormData()
  formData.append('project_id', projectId)
  formData.append('project_name', projectName)
  formData.append('file', file)

  const res = await fetch(`${BASE_URL}/api/v1/projects/upload-doc`, {
    method: 'POST',
    body: formData,
  })

  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Upload failed')
  // Returns: { status, message, chunks_added, project_id, version, is_new_version }
  return data
}

export async function compareVersions(projectId, filename, versionA, versionB) {
  const res = await fetch(`${BASE_URL}/api/v1/projects/${projectId}/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename, version_a: versionA, version_b: versionB }),
  })

  // Check content type before parsing JSON
  const contentType = res.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) {
    const text = await res.text()
    throw new Error(`Lỗi server: ${res.status} - ${text.substring(0, 100)}`)
  }

  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Compare failed')
  return data
}

export async function fetchVersionHistory(projectId) {
  const res = await fetch(`${BASE_URL}/api/v1/projects/${projectId}/versions`)
  if (!res.ok) throw new Error('Failed to fetch versions')
  return res.json()
}

/**
 * Stream chat response via SSE.
 * Calls onChunk(text) for each streamed chunk.
 * Calls onDone() when stream ends.
 * Calls onError(err) on failure.
 */
export async function streamChat({ projectId, userRole, message, history, onChunk, onDone, onError }) {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 180000) // 180s timeout

  try {
    console.log('[streamChat] Sending request to:', `${BASE_URL}/api/v1/chat/stream`)
    const res = await fetch(`${BASE_URL}/api/v1/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_id: projectId,
        user_role: userRole,
        message,
        history: history.map(m => ({ role: m.role, content: m.content })),
      }),
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    console.log('[streamChat] Response status:', res.status, 'ok:', res.ok)
    console.log('[streamChat] Response headers:', Object.fromEntries(res.headers.entries()))

    if (!res.ok) {
      const errorText = await res.text()
      console.error('[streamChat] Error response body:', errorText)
      throw new Error(`Server error: ${res.status} - ${errorText.substring(0, 100)}`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let chunkCount = 0
    let totalChars = 0

    console.log('[streamChat] Starting to read stream...')

    while (true) {
      const { value, done } = await reader.read()

      if (done) {
        console.log('[streamChat] Stream done signal received')
        break
      }

      const text = decoder.decode(value, { stream: true })
      console.log('[streamChat] Received raw data (' + value.length + ' bytes):', text.substring(0, 200))

      buffer += text
      const lines = buffer.split('\n\n')
      buffer = lines.pop() // Keep incomplete line in buffer

      for (const line of lines) {
        if (!line.startsWith('data: ')) {
          console.warn('[streamChat] Non-data line:', line.substring(0, 50))
          continue
        }
        try {
          const jsonStr = line.slice(6)
          const json = JSON.parse(jsonStr)
          console.log('[streamChat] Parsed JSON:', json)

          if (json.error) {
            console.error('[streamChat] Error from server:', json.error)
            onError(new Error(json.error))
            return
          }
          if (json.done) {
            console.log(`[streamChat] Done signal received, ${chunkCount} chunks, ${totalChars} chars`)
            onDone()
            return
          }
          if (json.text) {
            chunkCount++
            totalChars += json.text.length
            console.log(`[streamChat] Chunk ${chunkCount}: ${json.text.substring(0, 50)}...`)
            onChunk(json.text)
          }
        } catch (parseErr) {
          console.warn('[streamChat] Failed to parse line:', line.substring(0, 100), 'Error:', parseErr.message)
        }
      }
    }

    console.log(`[streamChat] Stream completed: ${chunkCount} chunks, ${totalChars} chars`)
    onDone()
  } catch (err) {
    clearTimeout(timeoutId)
    if (err.name === 'AbortError') {
      console.error('[streamChat] Request timed out after 180s')
      onError(new Error('Yêu cầu hết thời gian (timeout). Vui lòng thử lại.'))
    } else {
      console.error('[streamChat] Error:', err)
      onError(err)
    }
  }
}
