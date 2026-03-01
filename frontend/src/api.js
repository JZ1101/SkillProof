const API = 'http://localhost:8000/api'

async function request(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail || `Request failed (${res.status})`)
  }
  return res.json()
}

export async function fetchTrades() {
  return request(await fetch(`${API}/trades`))
}

export async function fetchTasks(tradeKey) {
  return request(await fetch(`${API}/trades/${tradeKey}/tasks`))
}

export async function createUser(name, email) {
  const form = new FormData()
  form.append('name', name)
  form.append('email', email)
  return request(await fetch(`${API}/users`, { method: 'POST', body: form }))
}

export async function startCertification(userId, trade) {
  const form = new FormData()
  form.append('user_id', userId)
  form.append('trade', trade)
  return request(await fetch(`${API}/certifications`, { method: 'POST', body: form }))
}

export async function uploadFile(file) {
  const form = new FormData()
  form.append('file', file)
  return request(await fetch(`${API}/upload`, { method: 'POST', body: form }))
}

export async function assessTask(certId, taskId, trade, filePath) {
  const form = new FormData()
  form.append('certification_id', certId)
  form.append('task_id', taskId)
  form.append('trade', trade)
  form.append('file_path', filePath)
  return request(await fetch(`${API}/assess`, { method: 'POST', body: form }))
}

export async function skipTask(certId, taskId, score) {
  const form = new FormData()
  form.append('certification_id', certId)
  form.append('task_id', taskId)
  form.append('score', score)
  return request(await fetch(`${API}/skip`, { method: 'POST', body: form }))
}

export async function generateCorrections(taskResultId) {
  const form = new FormData()
  form.append('task_result_id', taskResultId)
  return request(await fetch(`${API}/corrections/generate`, { method: 'POST', body: form }))
}

export async function issueCertificate(certId, workerName) {
  const form = new FormData()
  form.append('certification_id', certId)
  form.append('worker_name', workerName)
  return request(await fetch(`${API}/certificate`, { method: 'POST', body: form }))
}

// ---- Organisation / B2B ----

export async function createOrg(name, logoUrl) {
  const form = new FormData()
  form.append('name', name)
  if (logoUrl) form.append('logo_url', logoUrl)
  return request(await fetch(`${API}/orgs`, { method: 'POST', body: form }))
}

export async function getOrg(slug) {
  return request(await fetch(`${API}/orgs/${slug}`))
}

export async function getCustomRubric(slug, trade) {
  return request(await fetch(`${API}/orgs/${slug}/rubrics/${trade}`))
}

export async function saveCustomRubric(slug, trade, rubric, passThreshold) {
  const form = new FormData()
  form.append('trade', trade)
  form.append('rubric_json', JSON.stringify(rubric))
  form.append('pass_threshold', passThreshold)
  return request(await fetch(`${API}/orgs/${slug}/rubrics`, { method: 'POST', body: form }))
}

export async function getOrgAssessment(slug, trade) {
  return request(await fetch(`${API}/assess/${slug}/${trade}`))
}

export async function getOrgSubmissions(slug) {
  return request(fetch(`${API}/orgs/${slug}/submissions`))
}
