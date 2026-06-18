const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

async function readJson(response) {
  if (response.status === 204) {
    return null
  }
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.detail || 'Request failed')
  }
  return data
}

export async function listBuckets() {
  const response = await fetch(`${API_BASE}/api/buckets`)
  return readJson(response)
}

export async function createBucket(name) {
  const response = await fetch(`${API_BASE}/api/buckets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  return readJson(response)
}

export async function listObjects(bucketId) {
  const response = await fetch(`${API_BASE}/api/buckets/${bucketId}/objects`)
  return readJson(response)
}

export async function createFolder(bucketId, path) {
  const formData = new FormData()
  formData.append('path', path)

  const response = await fetch(`${API_BASE}/api/buckets/${bucketId}/objects/folders`, {
    method: 'POST',
    body: formData,
  })
  return readJson(response)
}

export async function uploadObject(bucketId, { key, file, metadata }) {
  const formData = new FormData()
  formData.append('key', key)
  formData.append('file', file)
  if (metadata?.trim()) {
    formData.append('metadata', metadata)
  }

  const response = await fetch(`${API_BASE}/api/buckets/${bucketId}/objects`, {
    method: 'POST',
    body: formData,
  })
  return readJson(response)
}

export async function deleteObject(bucketId, objectId) {
  const response = await fetch(`${API_BASE}/api/buckets/${bucketId}/objects/${objectId}`, {
    method: 'DELETE',
  })
  return readJson(response)
}

export async function deleteObjectsBulk(bucketId, objectIds) {
  const response = await fetch(`${API_BASE}/api/buckets/${bucketId}/objects/delete-bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ object_ids: objectIds }),
  })
  return readJson(response)
}

export async function deleteBucketContents(bucketId) {
  const response = await fetch(`${API_BASE}/api/buckets/${bucketId}/objects`, {
    method: 'DELETE',
  })
  return readJson(response)
}

export async function renameBucket(bucketId, newName) {
  const response = await fetch(`${API_BASE}/api/buckets/${bucketId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: newName }),
  })
  return readJson(response)
}

export async function deleteBucket(bucketId) {
  const response = await fetch(`${API_BASE}/api/buckets/${bucketId}`, {
    method: 'DELETE',
  })
  return readJson(response)
}
