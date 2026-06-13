const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
  try {
    const res = await fetch(`${BASE_URL}/api/v1/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_id: projectId,
        user_role: userRole,
        message,
        history: history.map(m => ({ role: m.role, content: m.content })),
      }),
    })

    if (!res.ok) {
      throw new Error(`Server error: ${res.status}`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop() // Keep incomplete line in buffer

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const json = JSON.parse(line.slice(6))
          if (json.error) {
            onError(new Error(json.error))
            return
          }
          if (json.done) {
            onDone()
            return
          }
          if (json.text) {
            onChunk(json.text)
          }
        } catch {
          // Skip malformed SSE line
        }
      }
    }

    onDone()
  } catch (err) {
    onError(err)
  }
}
