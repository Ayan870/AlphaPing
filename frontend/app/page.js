// frontend/app/page.js
'use client'
import { useState, useEffect } from 'react'
import axios from 'axios'
import CandleChart from './components/CandleChart'

const API = 'http://localhost:8000'

export default function Dashboard() {
  const [signals, setSignals]         = useState([])
  const [pending, setPending]         = useState([])
  const [subscribers, setSubscribers] = useState([])
  const [health, setHealth]           = useState(null)
  const [loading, setLoading]         = useState(true)
  const [running, setRunning]         = useState(false)
  const [activeTab, setActiveTab]     = useState('dashboard')
  const [activeModel, setActiveModel] = useState('ollama')
  const [performance, setPerformance] = useState(null)

  const fetchData = async () => {
    try {
      const [healthRes, signalsRes, pendingRes, subsRes, modelRes, perfRes] = await Promise.all([
        axios.get(`${API}/health`),
        axios.get(`${API}/signals/`),
        axios.get(`${API}/signals/pending`),
        axios.get(`${API}/subscribers/`),
        axios.get(`${API}/signals/model/status`),
        axios.get(`${API}/signals/performance/summary`),
      ])
      setHealth(healthRes.data)
      setSignals(signalsRes.data.signals || [])
      setPending(pendingRes.data.pending || [])
      setSubscribers(subsRes.data.subscribers || [])
      setActiveModel(modelRes.data.active_model || 'ollama')
      setPerformance(perfRes.data)
    } catch (err) {
      console.error('Failed to fetch data:', err)
    } finally {
      setLoading(false)
    }
  }

  const runSignal = async () => {
    setRunning(true)
    try {
      await axios.post(`${API}/signals/run`)
      alert('Pipeline started! Check pending signals in 30 seconds.')
      setTimeout(fetchData, 30000)
    } catch (err) {
      alert('Failed to run pipeline')
    } finally {
      setRunning(false)
    }
  }

  const approveSignal = async (threadId, approved) => {
    try {
      await axios.post(`${API}/signals/approve/${threadId}`, {
        approved,
        feedback: approved ? 'Approved from dashboard' : 'Rejected from dashboard'
      })
      alert(approved ? '✅ Signal approved and sent!' : '❌ Signal rejected')
      fetchData()
    } catch (err) {
      alert('Failed to process signal')
    }
  }

  const switchModel = async (model) => {
    try {
      await axios.post(`${API}/signals/model/switch/${model}`)
      setActiveModel(model)
    } catch (err) {
      alert('Failed to switch model')
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 3000)
    return () => clearInterval(interval)
  }, [])

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <p className="text-white text-xl">Loading AlphaPing...</p>
    </div>
  )

  const sentSignals    = signals.filter(s => s.delivery_status === 'sent')
  const noTradeSignals = signals.filter(s => s.delivery_status === 'no_trade')
  const latestSignal   = sentSignals.length > 0 ? sentSignals[0] : null

  return (
    <div className="min-h-screen bg-gray-950 text-white">

      {/* ── Header ── */}
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-blue-400">⚡ AlphaPing</h1>
            <p className="text-gray-400 text-sm">WhatsApp-First Crypto Signal Copilot</p>
          </div>
          <div className="flex items-center gap-4">

            {/* Model Switcher */}
            <div className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
              <button
                onClick={() => switchModel('ollama')}
                className={`px-3 py-1 rounded text-xs font-medium transition ${
                  activeModel === 'ollama'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                🦙 Ollama
              </button>
              <button
                onClick={() => switchModel('gemini')}
                className={`px-3 py-1 rounded text-xs font-medium transition ${
                  activeModel === 'gemini'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                ✨ Gemini
              </button>
            </div>

            {/* Backend Status */}
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
              health?.status === 'healthy'
                ? 'bg-green-900 text-green-400'
                : 'bg-red-900 text-red-400'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                health?.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
              }`}></div>
              {health?.status === 'healthy' ? 'Backend Online' : 'Backend Offline'}
            </div>

            {/* Run Pipeline */}
            <button
              onClick={runSignal}
              disabled={running}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-4 py-2 rounded-lg text-sm font-medium transition"
            >
              {running ? '⏳ Running...' : '🚀 Run Signal Pipeline'}
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mt-4">
          {['dashboard', 'pending', 'signals', 'subscribers'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm capitalize transition ${
                activeTab === tab
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab}
              {tab === 'pending' && pending.length > 0 && (
                <span className="ml-2 bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                  {pending.length}
                </span>
              )}
            </button>
          ))}
        </div>
      </header>

      <main className="p-6">

        {/* ── Dashboard Tab ── */}
        {activeTab === 'dashboard' && (
          <div>

            {/* Main Stats */}
            <div className="grid grid-cols-4 gap-4 mb-4">
              {[
                { label: 'Total Signals', value: signals.length,                    color: 'blue'   },
                { label: 'Signals Sent',  value: sentSignals.length,                color: 'green'  },
                { label: 'Win Rate',      value: `${performance?.win_rate || 0}%`,  color: 'yellow' },
                { label: 'Subscribers',   value: subscribers.length,                color: 'purple' },
              ].map(stat => (
                <div key={stat.label}
                  className="bg-gray-900 rounded-xl p-4 border border-gray-800">
                  <p className="text-gray-400 text-sm">{stat.label}</p>
                  <p className={`text-3xl font-bold mt-1 text-${stat.color}-400`}>
                    {stat.value}
                  </p>
                </div>
              ))}
            </div>

            {/* Performance Row */}
            {performance && (
              <div className="grid grid-cols-4 gap-4 mb-6">
                {[
                  { label: '✅ Wins',    value: performance.wins,    color: 'green'  },
                  { label: '❌ Losses',  value: performance.losses,  color: 'red'    },
                  { label: '⚡ Partial', value: performance.partial, color: 'yellow' },
                  { label: '⏳ Pending', value: performance.pending, color: 'gray'   },
                ].map(stat => (
                  <div key={stat.label}
                    className="bg-gray-900 rounded-xl p-3 border border-gray-800">
                    <p className="text-gray-400 text-xs">{stat.label}</p>
                    <p className={`text-2xl font-bold mt-1 text-${stat.color}-400`}>
                      {stat.value}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {/* Live Chart */}
            <div className="mb-6">
              <CandleChart activeSignal={latestSignal} />
            </div>

            {/* Pending Alert */}
            {pending.length > 0 && (
              <div className="bg-yellow-900 border border-yellow-700 rounded-xl p-4 mb-6">
                <p className="text-yellow-400 font-bold">
                  🔔 {pending.length} signal(s) waiting for your approval!
                </p>
                <button
                  onClick={() => setActiveTab('pending')}
                  className="mt-2 bg-yellow-600 hover:bg-yellow-700 px-4 py-2 rounded-lg text-sm"
                >
                  Review Now →
                </button>
              </div>
            )}

            {/* Recent Signals */}
            <div className="bg-gray-900 rounded-xl border border-gray-800">
              <div className="p-4 border-b border-gray-800">
                <h2 className="font-bold text-lg">Recent Signal Runs</h2>
              </div>
              <div className="divide-y divide-gray-800">
                {signals.slice(0, 5).map(signal => (
                  <div key={signal.id}
                    className="p-4 flex items-center justify-between">
                    <div>
                      <span className={`text-sm font-bold ${
                        signal.direction === 'LONG'  ? 'text-green-400' :
                        signal.direction === 'SHORT' ? 'text-red-400'   :
                        'text-gray-400'
                      }`}>
                        {signal.direction === 'NO_TRADE' ? '⏭ NO TRADE' :
                         signal.direction === 'LONG'     ? '🟢 LONG'    : '🔴 SHORT'}
                      </span>
                      <span className="text-gray-400 ml-2">{signal.pair || 'N/A'}</span>
                      {signal.confidence > 0 && (
                        <span className="text-gray-500 ml-2 text-sm">
                          {signal.confidence}/100
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        signal.delivery_status === 'sent'     ? 'bg-green-900 text-green-400' :
                        signal.delivery_status === 'no_trade' ? 'bg-gray-800 text-gray-400'  :
                        signal.delivery_status === 'rejected' ? 'bg-red-900 text-red-400'    :
                        'bg-yellow-900 text-yellow-400'
                      }`}>
                        {signal.delivery_status}
                      </span>
                      <span className="text-gray-600 text-xs">
                        {signal.created_at?.slice(0, 16).replace('T', ' ')}
                      </span>
                    </div>
                  </div>
                ))}
                {signals.length === 0 && (
                  <p className="p-4 text-gray-500 text-center">
                    No signals yet. Click Run Signal Pipeline to start.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── Pending Tab ── */}
        {activeTab === 'pending' && (
          <div>
            <h2 className="text-xl font-bold mb-4">
              🔔 Pending Approval ({pending.length})
            </h2>
            {pending.length === 0 ? (
              <div className="bg-gray-900 rounded-xl border border-gray-800 p-8 text-center">
                <p className="text-gray-400">No signals waiting for approval.</p>
                <p className="text-gray-600 text-sm mt-2">
                  Run the pipeline to generate a new signal.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {pending.map(signal => (
                  <div key={signal.thread_id}
                    className="bg-gray-900 rounded-xl border border-yellow-700 p-6">
                    <div className="flex items-center gap-3 mb-3">
                      <span className={`text-xl font-bold ${
                        signal.direction === 'LONG' ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {signal.direction === 'LONG' ? '🟢 LONG' : '🔴 SHORT'}
                      </span>
                      <span className="text-white font-bold">{signal.pair}</span>
                      <span className="bg-blue-900 text-blue-400 px-2 py-1 rounded text-sm">
                        {signal.confidence}/100 confidence
                      </span>
                      <span className="bg-gray-800 text-gray-400 px-2 py-1 rounded text-sm">
                        {signal.setup_type}
                      </span>
                    </div>
                    <p className="text-gray-400 text-sm mb-4">{signal.research_summary}</p>

                    {/* Signal levels */}
                    {signal.entry_low && (
                      <div className="grid grid-cols-3 gap-2 mb-4 text-xs">
                        <div className="bg-green-900 rounded p-2">
                          <p className="text-green-400">Entry</p>
                          <p className="text-white font-bold">
                            ${signal.entry_low?.toLocaleString()} - ${signal.entry_high?.toLocaleString()}
                          </p>
                        </div>
                        <div className="bg-red-900 rounded p-2">
                          <p className="text-red-400">Stop Loss</p>
                          <p className="text-white font-bold">${signal.stop_loss?.toLocaleString()}</p>
                        </div>
                        <div className="bg-blue-900 rounded p-2">
                          <p className="text-blue-400">TP1 / TP2 / TP3</p>
                          <p className="text-white font-bold">
                            ${signal.tp1?.toLocaleString()} / ${signal.tp2?.toLocaleString()} / ${signal.tp3?.toLocaleString()}
                          </p>
                        </div>
                      </div>
                    )}

                    <div className="flex gap-3">
                      <button
                        onClick={() => approveSignal(signal.thread_id, true)}
                        className="bg-green-600 hover:bg-green-700 px-6 py-2 rounded-lg font-medium transition"
                      >
                        ✅ Approve & Send
                      </button>
                      <button
                        onClick={() => approveSignal(signal.thread_id, false)}
                        className="bg-red-600 hover:bg-red-700 px-6 py-2 rounded-lg font-medium transition"
                      >
                        ❌ Reject
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Signals Tab ── */}
        {activeTab === 'signals' && (
          <div>
            <h2 className="text-xl font-bold mb-4">
              📊 All Signals ({signals.length})
            </h2>
            <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-800">
                  <tr>
                    {['Pair','Direction','Confidence','Setup','Status','Result','Date'].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-gray-400 text-sm">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {signals.map(signal => {
                    let perfLog = {}
                    try { perfLog = JSON.parse(signal.performance_log || '{}') } catch {}
                    return (
                      <tr key={signal.id} className="hover:bg-gray-800 transition">
                        <td className="px-4 py-3 text-sm">{signal.pair || '—'}</td>
                        <td className="px-4 py-3">
                          <span className={`text-sm font-bold ${
                            signal.direction === 'LONG'  ? 'text-green-400' :
                            signal.direction === 'SHORT' ? 'text-red-400'   :
                            'text-gray-500'
                          }`}>
                            {signal.direction}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-300">
                          {signal.confidence || 0}/100
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-400">
                          {signal.setup_type || '—'}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            signal.delivery_status === 'sent'     ? 'bg-green-900 text-green-400' :
                            signal.delivery_status === 'no_trade' ? 'bg-gray-800 text-gray-500'  :
                            signal.delivery_status === 'rejected' ? 'bg-red-900 text-red-400'    :
                            'bg-yellow-900 text-yellow-400'
                          }`}>
                            {signal.delivery_status}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          {perfLog.result && (
                            <span className={`text-xs px-2 py-1 rounded-full ${
                              perfLog.result === 'win'     ? 'bg-green-900 text-green-400' :
                              perfLog.result === 'loss'    ? 'bg-red-900 text-red-400'    :
                              perfLog.result === 'partial' ? 'bg-yellow-900 text-yellow-400' :
                              'bg-gray-800 text-gray-500'
                            }`}>
                              {perfLog.result}
                              {perfLog.final_pnl ? ` (${perfLog.final_pnl > 0 ? '+' : ''}${perfLog.final_pnl}%)` : ''}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-600">
                          {signal.created_at?.slice(0,16).replace('T',' ')}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
              {signals.length === 0 && (
                <p className="p-8 text-center text-gray-500">No signals yet.</p>
              )}
            </div>
          </div>
        )}

        {/* ── Subscribers Tab ── */}
        {activeTab === 'subscribers' && (
          <div>
            <h2 className="text-xl font-bold mb-4">
              👥 Subscribers ({subscribers.length})
            </h2>

            {/* Add subscriber */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 mb-4">
              <h3 className="font-bold mb-3">Add Test Subscriber</h3>
              <div className="flex gap-3">
                <input
                  id="phone"
                  type="text"
                  placeholder="+923001234567"
                  className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white flex-1"
                />
                <select
                  id="plan"
                  className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                >
                  <option value="free">Free</option>
                  <option value="pro">Pro</option>
                  <option value="vip">VIP</option>
                </select>
                <button
                  onClick={async () => {
                    const phone = document.getElementById('phone').value
                    const plan  = document.getElementById('plan').value
                    if (!phone) return alert('Enter phone number')
                    await axios.post(`${API}/subscribers/`, { phone, plan })
                    fetchData()
                  }}
                  className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition"
                >
                  Add
                </button>
              </div>
            </div>

            {/* Subscribers list */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-800">
                  <tr>
                    {['Phone','Plan','Status','Joined'].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-gray-400 text-sm">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {subscribers.map(sub => (
                    <tr key={sub.id} className="hover:bg-gray-800 transition">
                      <td className="px-4 py-3 text-sm">{sub.phone}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          sub.plan === 'vip' ? 'bg-purple-900 text-purple-400' :
                          sub.plan === 'pro' ? 'bg-blue-900 text-blue-400'    :
                          'bg-gray-800 text-gray-400'
                        }`}>
                          {sub.plan?.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          sub.active
                            ? 'bg-green-900 text-green-400'
                            : 'bg-red-900 text-red-400'
                        }`}>
                          {sub.active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-600">
                        {sub.joined_at?.slice(0,10)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {subscribers.length === 0 && (
                <p className="p-8 text-center text-gray-500">No subscribers yet.</p>
              )}
            </div>
          </div>
        )}

      </main>
    </div>
  )
}