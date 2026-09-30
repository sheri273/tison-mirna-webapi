import { useEffect, useState } from 'react'
import './App.css'

const API_URL = 'http://localhost:8000'

function App() {
  const [apiStatus, setApiStatus] = useState('Checking...')
  const [mirnaCount, setMirnaCount] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/`)
      .then((response) => {
        if (!response.ok) throw new Error('API error')
        return response.json()
      })
      .then(() => setApiStatus('Connected'))
      .catch(() => setApiStatus('Offline'))

    fetch(`${API_URL}/mirnas/count`)
      .then((response) => {
        if (!response.ok) throw new Error('Count error')
        return response.json()
      })
      .then((data) => {
        setMirnaCount(data.count ?? data.total ?? null)
      })
      .catch(() => setMirnaCount(null))
  }, [])

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>TISON miRNA WebAPI</h1>
          <p>miRNA analysis and cancer expression platform</p>
        </div>

        <div className={`status ${apiStatus === 'Connected' ? 'online' : ''}`}>
          ● API {apiStatus}
        </div>
      </header>

      <main>
        <section className="hero">
          <h2>miRNA Research Dashboard</h2>
          <p>
            Explore miRNA information, expression data, and differential
            expression results through the TISON WebAPI.
          </p>
        </section>

        <section className="cards">
          <div className="card">
            <h3>miRNA Database</h3>
            <p>
              Access the curated miRNA database and search for individual
              miRNAs.
            </p>
            <strong>
              {mirnaCount !== null ? mirnaCount.toLocaleString() : '—'}
            </strong>
            <span>miRNAs available</span>
          </div>

          <div className="card">
            <h3>Expression Analysis</h3>
            <p>
              Explore miRNA expression across TCGA-BRCA sample types.
            </p>
            <span>Primary Tumor • Normal • Metastatic</span>
          </div>

          <div className="card">
            <h3>Differential Expression</h3>
            <p>
              Review fold change, log2 fold change, p-values, and FDR results.
            </p>
            <span>TCGA-BRCA</span>
          </div>
        </section>

        <section className="quick-links">
          <h2>API Resources</h2>

          <div className="links">
            <a href={`${API_URL}/docs`} target="_blank" rel="noreferrer">
              Swagger API Documentation
            </a>

            <a href={`${API_URL}/mirnas`} target="_blank" rel="noreferrer">
              miRNA Endpoint
            </a>

            <a
              href={`${API_URL}/expression/differential/top`}
              target="_blank"
              rel="noreferrer"
            >
              Top Differential miRNAs
            </a>
          </div>
        </section>
      </main>

      <footer>
        <p>TISON miRNA WebAPI • Bioinformatics Research Platform</p>
      </footer>
    </div>
  )
}

export default App
