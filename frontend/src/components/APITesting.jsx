import { useState, useCallback } from 'react'
import axios from 'axios'

// Use relative path for production (same-origin), localhost for dev
const API_BASE = import.meta.env.DEV ? 'http://localhost:8000/api/v1' : '/api/v1'

export default function APITesting({ projectId, projectName }) {
  const [uploading, setUploading] = useState(false)
  const [endpoints, setEndpoints] = useState([])
  const [selectedEndpoints, setSelectedEndpoints] = useState(new Set())
  const [results, setResults] = useState(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setUploading(true)
    setError('')

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${API_BASE}/test/upload-spec`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      setEndpoints(response.data.endpoints)
      setResults(null)
      setSelectedEndpoints(new Set())
      console.log('Parsed endpoints:', response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to parse spec file')
    } finally {
      setUploading(false)
    }
  }

  const toggleEndpoint = (id) => {
    const newSet = new Set(selectedEndpoints)
    if (newSet.has(id)) {
      newSet.delete(id)
    } else {
      newSet.add(id)
    }
    setSelectedEndpoints(newSet)
  }

  const toggleAll = () => {
    if (selectedEndpoints.size === endpoints.length) {
      setSelectedEndpoints(new Set())
    } else {
      setSelectedEndpoints(new Set(endpoints.map(e => {
        // Include summary in endpoint ID for better test names
        if (e.summary) {
          return `${e.method}:${e.path}:${e.summary}`
        }
        return `${e.method}:${e.path}`
      })))
    }
  }

  const runTests = async () => {
    if (selectedEndpoints.size === 0) {
      setError('Please select at least one endpoint')
      return
    }

    setRunning(true)
    setError('')

    try {
      const response = await axios.post(`${API_BASE}/test/bulk-run`, {
        endpoint_ids: Array.from(selectedEndpoints),
        run_tests: true,
        create_bugs: true
      })

      setResults(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to run tests')
    } finally {
      setRunning(false)
    }
  }

  const generateTests = async () => {
    if (selectedEndpoints.size === 0) {
      setError('Please select at least one endpoint')
      return
    }

    setRunning(true)
    setError('')

    try {
      const response = await axios.post(`${API_BASE}/test/bulk-generate`, {
        endpoint_ids: Array.from(selectedEndpoints),
        run_tests: false
      })

      setResults(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate tests')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="flex-1 overflow-auto bg-[#0d0f12] text-slate-300 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white mb-2">API Testing</h1>
          <p className="text-slate-400 text-sm">
            Upload Swagger/OpenAPI spec or Postman collection to auto-generate and run tests
          </p>
        </div>

        {/* Upload Section */}
        <div className="mb-6 p-6 border border-slate-700 rounded-lg bg-slate-800/30">
          <label className="block">
            <span className="text-sm font-medium text-slate-300 mb-2 block">
              Upload API Spec (OpenAPI/Swagger or Postman Collection)
            </span>
            <input
              type="file"
              accept=".json,.yaml,.yml"
              onChange={handleFileUpload}
              disabled={uploading}
              className="block w-full text-sm text-slate-400
                file:mr-4 file:py-2 file:px-4
                file:rounded-full file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-600 file:text-white
                hover:file:bg-blue-700
                disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </label>
          {uploading && <p className="text-sm text-blue-400 mt-2">Parsing spec file...</p>}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-900/30 border border-red-700 rounded-lg">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Endpoints List */}
        {endpoints.length > 0 && (
          <>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">
                Endpoints ({endpoints.length})
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={toggleAll}
                  className="px-3 py-1.5 text-sm rounded border border-slate-600 hover:border-slate-400 transition-colors"
                >
                  {selectedEndpoints.size === endpoints.length ? 'Deselect All' : 'Select All'}
                </button>
                <button
                  onClick={generateTests}
                  disabled={selectedEndpoints.size === 0 || running}
                  className="px-4 py-1.5 text-sm rounded bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Generate Tests
                </button>
                <button
                  onClick={runTests}
                  disabled={selectedEndpoints.size === 0 || running}
                  className="px-4 py-1.5 text-sm rounded bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-white"
                >
                  {running ? 'Running...' : 'Run Tests'}
                </button>
              </div>
            </div>

            <div className="border border-slate-700 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-slate-800/50">
                  <tr>
                    <th className="text-left p-3 w-12"></th>
                    <th className="text-left p-3 w-24">Method</th>
                    <th className="text-left p-3">Path</th>
                    <th className="text-left p-3">Summary</th>
                  </tr>
                </thead>
                <tbody>
                  {endpoints.map((ep, idx) => {
                    const id = ep.summary ? `${ep.method}:${ep.path}:${ep.summary}` : `${ep.method}:${ep.path}`
                    const selected = selectedEndpoints.has(id)
                    return (
                      <tr
                        key={idx}
                        className={`border-t border-slate-700/50 ${selected ? 'bg-blue-900/20' : ''}`}
                      >
                        <td className="p-3">
                          <input
                            type="checkbox"
                            checked={selected}
                            onChange={() => toggleEndpoint(id)}
                            className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-blue-500"
                          />
                        </td>
                        <td className="p-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium
                            ${ep.method === 'GET' ? 'bg-green-900/40 text-green-400' : ''}
                            ${ep.method === 'POST' ? 'bg-blue-900/40 text-blue-400' : ''}
                            ${ep.method === 'PUT' ? 'bg-yellow-900/40 text-yellow-400' : ''}
                            ${ep.method === 'DELETE' ? 'bg-red-900/40 text-red-400' : ''}
                          `}>
                            {ep.method}
                          </span>
                        </td>
                        <td className="p-3 font-mono text-slate-400">{ep.path}</td>
                        <td className="p-3 text-slate-500 truncate max-w-xs">
                          {ep.summary || ep.description || '-'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {/* Results */}
            {results && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold text-white mb-4">Test Results</h3>

                {/* Summary */}
                <div className="grid grid-cols-5 gap-4 mb-6">
                  <div className="p-4 bg-slate-800/50 rounded-lg text-center">
                    <div className="text-2xl font-bold text-white">{results.total_endpoints}</div>
                    <div className="text-xs text-slate-400">Total</div>
                  </div>
                  <div className="p-4 bg-slate-800/50 rounded-lg text-center">
                    <div className="text-2xl font-bold text-blue-400">{results.tests_generated}</div>
                    <div className="text-xs text-slate-400">Generated</div>
                  </div>
                  <div className="p-4 bg-slate-800/50 rounded-lg text-center">
                    <div className="text-2xl font-bold text-green-400">{results.passed}</div>
                    <div className="text-xs text-slate-400">Passed</div>
                  </div>
                  <div className="p-4 bg-slate-800/50 rounded-lg text-center">
                    <div className="text-2xl font-bold text-red-400">{results.failed}</div>
                    <div className="text-xs text-slate-400">Failed</div>
                  </div>
                  <div className="p-4 bg-slate-800/50 rounded-lg text-center">
                    <div className="text-2xl font-bold text-yellow-400">{results.errors}</div>
                    <div className="text-xs text-slate-400">Errors</div>
                  </div>
                </div>

                {/* Test Details */}
                {results.test_results.length > 0 && (
                  <div className="space-y-4">
                    {results.test_results.map((result, idx) => (
                      <div
                        key={idx}
                        className={`p-4 border rounded-lg ${
                          result.status === 'passed'
                            ? 'bg-green-900/20 border-green-700'
                            : result.status === 'failed'
                            ? 'bg-red-900/20 border-red-700'
                            : 'bg-yellow-900/20 border-yellow-700'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-semibold text-white">{result.test_name}</h4>
                          <span className={`text-xs px-2 py-1 rounded uppercase font-medium
                            ${result.status === 'passed' ? 'bg-green-700 text-green-200' : ''}
                            ${result.status === 'failed' ? 'bg-red-700 text-red-200' : ''}
                            ${result.status === 'error' ? 'bg-yellow-700 text-yellow-200' : ''}
                          `}>
                            {result.status}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mb-2">Duration: {result.duration.toFixed(2)}s</p>
                        {result.error_message && (
                          <p className="text-sm text-red-400 mb-2">{result.error_message}</p>
                        )}
                        <details className="text-xs">
                          <summary className="cursor-pointer text-blue-400 hover:text-blue-300 mb-1">
                            View output
                          </summary>
                          <pre className="mt-2 p-3 bg-slate-900 rounded overflow-x-auto text-slate-400 font-mono">
                            {result.output}
                          </pre>
                        </details>
                      </div>
                    ))}
                  </div>
                )}

                {/* Jira Tickets */}
                {results.jira_tickets && results.jira_tickets.length > 0 && (
                  <div className="mt-6">
                    <h4 className="text-sm font-semibold text-white mb-3">Jira Tickets Created</h4>
                    <div className="space-y-2">
                      {results.jira_tickets.map((ticket, idx) => (
                        <div key={idx} className="p-3 bg-purple-900/20 border border-purple-700 rounded-lg">
                          <p className="text-sm text-white">{ticket.ticket_key}: {ticket.message}</p>
                          {ticket.ticket_url && ticket.ticket_url !== 'N/A' && (
                            <a
                              href={ticket.ticket_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-purple-400 hover:text-purple-300"
                            >
                              Open in Jira →
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* Empty State */}
        {endpoints.length === 0 && !uploading && !error && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📄</div>
            <p className="text-slate-400 mb-4">No endpoints loaded yet</p>
            <p className="text-sm text-slate-500">
              Upload an OpenAPI spec or Postman collection to get started
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
