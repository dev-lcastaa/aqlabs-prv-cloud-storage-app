import { useEffect, useMemo, useState } from 'react'
import {
  createFolder,
  createBucket,
  deleteObject,
  deleteBucket,
  deleteObjectsBulk,
  deleteBucketContents,
  listBuckets,
  listObjects,
  uploadObject,
} from './lib/api'
import './App.css'

function App() {
  const [view, setView] = useState('home')
  const [buckets, setBuckets] = useState([])
  const [activeBucketId, setActiveBucketId] = useState('')
  const [objects, setObjects] = useState([])
  const [adminBucketId, setAdminBucketId] = useState('')
  const [adminBucketObjects, setAdminBucketObjects] = useState([])
  const [selectedObjectIds, setSelectedObjectIds] = useState([])
  const [bucketName, setBucketName] = useState('')
  const [objectKey, setObjectKey] = useState('')
  const [folderPath, setFolderPath] = useState('')
  const [objectMetadata, setObjectMetadata] = useState('')
  const [uploadFile, setUploadFile] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const activeBucket = useMemo(
    () => buckets.find((bucket) => bucket.id === activeBucketId) || null,
    [buckets, activeBucketId],
  )
  const activeAdminBucket = useMemo(
    () => buckets.find((bucket) => bucket.id === adminBucketId) || null,
    [buckets, adminBucketId],
  )

  async function loadBuckets(preferredBucketId = '') {
    const data = await listBuckets()
    setBuckets(data)

    if (preferredBucketId) {
      setActiveBucketId(preferredBucketId)
      return
    }

    if (!activeBucketId && data.length > 0) {
      setActiveBucketId(data[0].id)
      return
    }

    const stillExists = data.some((bucket) => bucket.id === activeBucketId)
    if (!stillExists) {
      setActiveBucketId(data[0]?.id ?? '')
    }
  }

  async function loadObjects(bucketId) {
    if (!bucketId) {
      setObjects([])
      setSelectedObjectIds([])
      return
    }
    const data = await listObjects(bucketId)
    setObjects(data)
    setSelectedObjectIds([])
  }

  async function openBucket(bucketId) {
    setActiveBucketId(bucketId)
    setView('bucket')
    setLoading(true)
    setError('')
    try {
      await loadObjects(bucketId)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function openAdmin() {
    setView('admin')
    setAdminBucketId('')
    setAdminBucketObjects([])
    setLoading(true)
    setError('')
    try {
      const bucketList = await listBuckets()
      setBuckets(bucketList)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function openAdminBucket(bucketId) {
    setAdminBucketId(bucketId)
    setView('admin-bucket')
    setLoading(true)
    setError('')
    try {
      const bucketObjects = await listObjects(bucketId)
      setAdminBucketObjects(bucketObjects)
    } catch (err) {
      setError(err.message)
      setAdminBucketObjects([])
    } finally {
      setLoading(false)
    }
  }

  async function onPurgeBucket() {
    if (!adminBucketId) return
    setError('')
    setLoading(true)
    try {
      await deleteBucketContents(adminBucketId)
      setAdminBucketObjects([])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function onDeleteBucket() {
    if (!adminBucketId) return
    setError('')
    setLoading(true)
    try {
      await deleteBucket(adminBucketId)
      await openAdmin()
      setView('admin')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    async function init() {
      setLoading(true)
      setError('')
      try {
        await loadBuckets()
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [])

  async function onCreateBucket(event) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const newBucket = await createBucket(bucketName.trim())
      setBucketName('')
      await loadBuckets(newBucket.id)
      await openBucket(newBucket.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function onUpload(event) {
    event.preventDefault()
    if (!activeBucketId) {
      setError('Create and select a bucket first')
      return
    }
    if (!uploadFile) {
      setError('Choose a file to upload')
      return
    }
    if (!objectKey.trim()) {
      setError('Provide an object key')
      return
    }

    setError('')
    setLoading(true)
    try {
      await uploadObject(activeBucketId, {
        key: objectKey.trim(),
        file: uploadFile,
        metadata: objectMetadata,
      })
      setUploadFile(null)
      setObjectKey('')
      setObjectMetadata('')
      const fileInput = document.getElementById('file-input')
      if (fileInput) {
        fileInput.value = ''
      }
      await loadObjects(activeBucketId)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function onCreateFolder(event) {
    event.preventDefault()
    if (!activeBucketId) {
      setError('Create and select a bucket first')
      return
    }
    if (!folderPath.trim()) {
      setError('Provide a folder path')
      return
    }
    setError('')
    setLoading(true)
    try {
      await createFolder(activeBucketId, folderPath.trim())
      setFolderPath('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function toggleSelection(objectId) {
    setSelectedObjectIds((current) => {
      if (current.includes(objectId)) {
        return current.filter((id) => id !== objectId)
      }
      return [...current, objectId]
    })
  }

  async function onDeleteSingle(objectId) {
    setError('')
    setLoading(true)
    try {
      await deleteObject(activeBucketId, objectId)
      await loadObjects(activeBucketId)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function onDeleteBulk() {
    if (selectedObjectIds.length === 0) {
      return
    }
    setError('')
    setLoading(true)
    try {
      const result = await deleteObjectsBulk(activeBucketId, selectedObjectIds)
      if (result.failed.length > 0) {
        setError(`Deleted ${result.deleted.length}, failed ${result.failed.length}`)
      }
      await loadObjects(activeBucketId)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function formatBytes(bytes) {
    if (bytes === 0) {
      return '0 B'
    }
    const sizes = ['B', 'KB', 'MB', 'GB']
    const unitIndex = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), sizes.length - 1)
    const value = bytes / 1024 ** unitIndex
    return `${value.toFixed(unitIndex === 0 ? 0 : 1)} ${sizes[unitIndex]}`
  }

  return (
    <div className="page-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Container Volume Storage</p>
          <h1>Aqlabs Object Store Command Center</h1>
          <p className="subtitle">
            Create bucket folders, upload keyed objects, and delete single or multiple objects.
          </p>
        </div>
        <div className="nav-row">
          <button type="button" className={view === 'home' ? 'nav-btn active' : 'nav-btn'} onClick={() => setView('home')}>
            Buckets
          </button>
          <button type="button" className={view.startsWith('admin') ? 'nav-btn active' : 'nav-btn'} onClick={openAdmin}>
            Admin
          </button>
          <span className="status-chip">{loading ? 'Working...' : 'Ready'}</span>
        </div>
      </header>

      {error ? <p className="error-banner">{error}</p> : null}

      {view === 'home' ? (
        <section className="home-layout">
          <article className="panel create-panel">
            <h2>Create Bucket</h2>
            <form className="stack create-row" onSubmit={onCreateBucket}>
              <input
                value={bucketName}
                onChange={(event) => setBucketName(event.target.value)}
                placeholder="new-bucket"
                minLength={3}
                required
              />
              <button type="submit" disabled={loading}>Create bucket</button>
            </form>
          </article>

          <article className="panel">
            <h2>Buckets</h2>
            <div className="bucket-grid">
              {buckets.map((bucket) => (
                <button key={bucket.id} type="button" className="tile bucket-tile" onClick={() => openBucket(bucket.id)}>
                  <span className="icon">🪣</span>
                  <div>
                    <strong>{bucket.name}</strong>
                    <small>{bucket.id.slice(0, 8)}</small>
                  </div>
                </button>
              ))}
              {buckets.length === 0 ? <p className="empty">No buckets found.</p> : null}
            </div>
          </article>
        </section>
      ) : null}

      {view === 'bucket' ? (
        <section className="panel wide">
          <div className="section-head">
            <h2>Objects {activeBucket ? `in ${activeBucket.name}` : ''}</h2>
            <button type="button" className="ghost" onClick={() => setView('home')}>Back to buckets</button>
          </div>

          <form className="upload-grid" onSubmit={onUpload}>
            <div className="folder-row">
              <input
                value={folderPath}
                onChange={(event) => setFolderPath(event.target.value)}
                placeholder="reports/2026"
              />
              <button type="button" onClick={onCreateFolder} disabled={loading || !activeBucketId}>
                Create folder
              </button>
            </div>
            <input
              id="file-input"
              type="file"
              onChange={(event) => setUploadFile(event.target.files?.[0] ?? null)}
              required
            />
            <input
              value={objectKey}
              onChange={(event) => setObjectKey(event.target.value)}
              placeholder="reports/2026/june.csv"
              required
            />
            <textarea
              value={objectMetadata}
              onChange={(event) => setObjectMetadata(event.target.value)}
              placeholder='{"owner":"ops","env":"dev"}'
              rows={3}
            />
            <button type="submit" disabled={loading || !activeBucketId}>Upload object</button>
          </form>

          <div className="actions-row">
            <button
              type="button"
              className="danger"
              onClick={onDeleteBulk}
              disabled={loading || selectedObjectIds.length === 0}
            >
              Delete selected ({selectedObjectIds.length})
            </button>
          </div>

          <div className="object-grid">
            {objects.map((object) => (
              <article key={object.id} className="tile object-tile">
                <label>
                  <input
                    type="checkbox"
                    checked={selectedObjectIds.includes(object.id)}
                    onChange={() => toggleSelection(object.id)}
                  />
                </label>
                <span className="icon">📦</span>
                <div className="tile-text">
                  <strong>{object.object_key}</strong>
                  <small>{formatBytes(object.size_bytes)} | {object.etag.slice(0, 10)}...</small>
                </div>
                <button type="button" className="danger ghost" onClick={() => onDeleteSingle(object.id)} disabled={loading}>
                  Delete
                </button>
              </article>
            ))}
            {objects.length === 0 ? <p className="empty">No objects in this bucket.</p> : null}
          </div>
        </section>
      ) : null}

      {view === 'admin' ? (
        <section className="panel">
          <h2>Buckets</h2>
          {buckets.length > 0 ? <p className="subtitle">Select a bucket to view contents.</p> : null}
          <div className="bucket-grid">
            {buckets.map((bucket) => (
              <button
                key={bucket.id}
                type="button"
                className={`tile bucket-tile ${adminBucketId === bucket.id ? 'admin-selected' : ''}`}
                onClick={() => openAdminBucket(bucket.id)}
              >
                <span className="icon">🪣</span>
                <div>
                  <strong>{bucket.name}</strong>
                  <small>{bucket.id.slice(0, 8)}</small>
                </div>
              </button>
            ))}
            {buckets.length === 0 ? <p className="empty">No buckets found.</p> : null}
          </div>
        </section>
      ) : null}

      {view === 'admin-bucket' ? (
        <section className="panel wide">
          <div className="section-head">
            <h2>Admin | Object Mapping {activeAdminBucket ? `for ${activeAdminBucket.name}` : ''}</h2>
            <div>
              <button type="button" className="ghost" onClick={() => setView('admin')}>Back to admin buckets</button>
              <button type="button" className="danger" onClick={onPurgeBucket} disabled={loading || !adminBucketId}>Purge contents</button>
              <button type="button" className="danger" onClick={onDeleteBucket} disabled={loading || !adminBucketId}>Delete bucket</button>
            </div>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Key Name</th>
                  <th>Size</th>
                  <th>ETag</th>
                  <th>Date Created</th>
                </tr>
              </thead>
              <tbody>
                {adminBucketObjects.map((obj) => (
                  <tr key={obj.id}>
                    <td className="mono">{obj.object_key}</td>
                    <td>{formatBytes(obj.size_bytes)}</td>
                    <td className="mono">{obj.etag}</td>
                    <td>{new Date(obj.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {adminBucketObjects.length === 0 ? <p className="empty">No mapped objects found for this bucket.</p> : null}
          </div>
        </section>
      ) : null}
    </div>
  )
}

export default App
