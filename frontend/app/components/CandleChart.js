// frontend/app/components/CandleChart.js
'use client'
import { useState, useEffect, useRef } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

export default function CandleChart({ activeSignal = null }) {
  const [selectedPair, setSelectedPair] = useState('BTCUSDT')
  const [candles, setCandles]           = useState([])
  const [currentPrice, setCurrentPrice] = useState(null)
  const [priceChange, setPriceChange]   = useState(null)
  const [loading, setLoading]           = useState(true)
  const plotRef                         = useRef(null)
  const wsRef                           = useRef(null)

  const PAIRS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']

  // Fetch historical candles from Binance REST API
  const fetchCandles = async (symbol) => {
    try {
      setLoading(true)
      const res = await axios.get(
        `https://api.binance.com/api/v3/klines`,
        { params: { symbol, interval: '1h', limit: 50 } }
      )
      const formatted = res.data.map(k => ({
        time:   new Date(k[0]).toISOString(),
        open:   parseFloat(k[1]),
        high:   parseFloat(k[2]),
        low:    parseFloat(k[3]),
        close:  parseFloat(k[4]),
        volume: parseFloat(k[5])
      }))
      setCandles(formatted)
      if (formatted.length > 0) {
        const latest = formatted[formatted.length - 1]
        const prev   = formatted[formatted.length - 2]
        setCurrentPrice(latest.close)
        setPriceChange(
          ((latest.close - prev.close) / prev.close * 100).toFixed(2)
        )
      }
    } catch (err) {
      console.error('Failed to fetch candles:', err)
    } finally {
      setLoading(false)
    }
  }

  // Connect to Binance WebSocket for live updates
  const connectWebSocket = (symbol) => {
    if (wsRef.current) wsRef.current.close()

    const ws = new WebSocket(
      `wss://stream.binance.com:9443/ws/${symbol.toLowerCase()}@kline_1h`
    )

    ws.onopen = () => console.log(`📡 Chart WebSocket connected: ${symbol}`)

    ws.onmessage = (event) => {
      const data   = JSON.parse(event.data)
      const candle = data.k

      const newCandle = {
        time:   new Date(candle.t).toISOString(),
        open:   parseFloat(candle.o),
        high:   parseFloat(candle.h),
        low:    parseFloat(candle.l),
        close:  parseFloat(candle.c),
        volume: parseFloat(candle.v)
      }

      setCurrentPrice(newCandle.close)
      setCandles(prev => {
        const updated = [...prev]
        const lastIdx = updated.length - 1
        if (lastIdx >= 0 && updated[lastIdx].time === newCandle.time) {
          updated[lastIdx] = newCandle  // update current candle
        } else if (candle.x) {
          updated.push(newCandle)       // new candle closed
          if (updated.length > 50) updated.shift()
        }
        return updated
      })
    }

    ws.onerror = (err) => console.error('WebSocket error:', err)
    ws.onclose = () => console.log('WebSocket closed')
    wsRef.current = ws
  }

  // Draw chart using Plotly
  useEffect(() => {
    if (candles.length === 0 || !plotRef.current) return

    const times   = candles.map(c => c.time)
    const opens   = candles.map(c => c.open)
    const highs   = candles.map(c => c.high)
    const lows    = candles.map(c => c.low)
    const closes  = candles.map(c => c.close)

    const candlestickTrace = {
      type: 'candlestick',
      x:    times,
      open:  opens,
      high:  highs,
      low:   lows,
      close: closes,
      name: selectedPair,
      increasing: { line: { color: '#26a69a' }, fillcolor: '#26a69a' },
      decreasing: { line: { color: '#ef5350' }, fillcolor: '#ef5350' },
    }

    // volume trace removed — chart will display candlesticks only

    // Build signal level lines if signal exists for current pair
    const shapes = []
    const annotations = []

    if (activeSignal && activeSignal.pair === selectedPair) {
      const lineConfigs = [
        { y: activeSignal.entry_low,  color: '#22c55e', label: 'Entry Low',  dash: 'solid' },
        { y: activeSignal.entry_high, color: '#22c55e', label: 'Entry High', dash: 'solid' },
        { y: activeSignal.stop_loss,  color: '#ef4444', label: 'Stop Loss',  dash: 'dash'  },
        { y: activeSignal.tp1,        color: '#3b82f6', label: 'TP1',        dash: 'dot'   },
        { y: activeSignal.tp2,        color: '#6366f1', label: 'TP2',        dash: 'dot'   },
        { y: activeSignal.tp3,        color: '#8b5cf6', label: 'TP3',        dash: 'dot'   },
      ]

      lineConfigs.forEach(({ y, color, label, dash }) => {
        if (!y) return
        shapes.push({
          type:    'line',
          x0:     times[0],
          x1:     times[times.length - 1],
          y0:     y,
          y1:     y,
          line:   { color, width: 1.5, dash },
          xref:   'x',
          yref:   'y',
        })
        annotations.push({
          x:          times[times.length - 1],
          y:          y,
          xref:       'x',
          yref:       'y',
          text:       `${label}: $${y.toLocaleString()}`,
          showarrow:  false,
          font:       { color, size: 10 },
          xanchor:    'right',
          yanchor:    'middle',
          bgcolor:    '#111827',
          borderpad:  2,
        })
      })
    }

    const layout = {
      paper_bgcolor: '#111827',
      plot_bgcolor:  '#111827',
      font:          { color: '#9ca3af', size: 11 },
      margin:        { t: 10, r: 20, b: 40, l: 60 },
      xaxis: {
        type:        'date',
        gridcolor:   '#1f2937',
        linecolor:   '#374151',
        rangeslider: { visible: false },
      },
      yaxis: {
        gridcolor:  '#1f2937',
        linecolor:  '#374151',
        side:       'right',
        tickformat: '.0f',
      },
      // no secondary y-axis (volume) — showing candles only
      legend:    { x: 0, y: 1, bgcolor: 'transparent' },
      hovermode: 'x unified',
      hoverlabel: {
        bgcolor: '#1f2937',
        font:    { color: '#fff' }
      },
      shapes,
      annotations,
    }

    const config = {
      responsive:     true,
      displaylogo:    false,
      modeBarButtons: [['zoom2d', 'pan2d', 'resetScale2d']],
    }

    import('plotly.js-dist-min').then(Plotly => {
      Plotly.react(
        plotRef.current,
        [candlestickTrace],
        layout,
        config
      )
    })
  }, [candles, selectedPair, activeSignal])

  // Switch pair
  useEffect(() => {
    fetchCandles(selectedPair)
    connectWebSocket(selectedPair)
    return () => { if (wsRef.current) wsRef.current.close() }
  }, [selectedPair])

  const getCoinName = (pair) => pair.replace('USDT', '')

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
      {/* Chart Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          {/* Pair selector */}
          <div className="flex gap-2">
            {PAIRS.map(pair => (
              <button
                key={pair}
                onClick={() => setSelectedPair(pair)}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition ${
                  selectedPair === pair
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:text-white'
                }`}
              >
                {getCoinName(pair)}
              </button>
            ))}
          </div>

          {/* Price display */}
          {currentPrice && (
            <div className="flex items-center gap-3">
              <span className="text-white text-xl font-bold">
                ${currentPrice.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })}
              </span>
              <span className={`text-sm font-medium px-2 py-1 rounded ${
                parseFloat(priceChange) >= 0
                  ? 'bg-green-900 text-green-400'
                  : 'bg-red-900 text-red-400'
              }`}>
                {parseFloat(priceChange) >= 0 ? '+' : ''}{priceChange}%
              </span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-gray-400 text-xs">Live • 1H Chart</span>
        </div>
      </div>

      {/* Chart */}
      {loading ? (
        <div className="h-96 flex items-center justify-center">
          <p className="text-gray-400">Loading chart data...</p>
        </div>
      ) : (
        <div ref={plotRef} style={{ height: '400px', width: '100%' }} />
      )}

      {/* Stats bar */}
      {candles.length > 0 && (
        <div className="flex gap-6 mt-3 pt-3 border-t border-gray-800">
          {[
            { label: 'Open',   value: candles[candles.length-1]?.open },
            { label: 'High',   value: candles[candles.length-1]?.high },
            { label: 'Low',    value: candles[candles.length-1]?.low },
            { label: 'Close',  value: candles[candles.length-1]?.close },
            { label: 'Volume', value: candles[candles.length-1]?.volume, isVol: true },
          ].map(stat => (
            <div key={stat.label}>
              <p className="text-gray-500 text-xs">{stat.label}</p>
              <p className="text-white text-sm font-medium">
                {stat.isVol
                  ? stat.value?.toLocaleString('en-US', { maximumFractionDigits: 0 })
                  : `$${stat.value?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                }
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}