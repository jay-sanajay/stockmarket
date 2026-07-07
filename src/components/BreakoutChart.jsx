import React, { useEffect, useRef } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from "recharts";

const BreakoutChart = ({ symbol, data, pdh, pdl, signals }) => {
  const chartRef = useRef();

  // Prepare chart data
  const chartData = data.map((candle, index) => ({
    time: new Date(candle.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    timestamp: candle.timestamp,
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
    volume: candle.volume,
    index: index
  }));

  // Find signals for this symbol
  const symbolSignals = signals.filter(signal => signal.symbol === symbol);

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="custom-tooltip" style={{
          backgroundColor: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '8px',
          padding: '12px',
          color: '#f8fafc'
        }}>
          <p style={{ margin: '0 0 8px 0', fontWeight: 'bold' }}>{`Time: ${label}`}</p>
          <p style={{ margin: '4px 0', color: '#10b981' }}>{`Open: ₹${data.open.toFixed(2)}`}</p>
          <p style={{ margin: '4px 0', color: '#ef4444' }}>{`High: ₹${data.high.toFixed(2)}`}</p>
          <p style={{ margin: '4px 0', color: '#3b82f6' }}>{`Low: ₹${data.low.toFixed(2)}`}</p>
          <p style={{ margin: '4px 0' }}>{`Close: ₹${data.close.toFixed(2)}`}</p>
          <p style={{ margin: '4px 0', color: '#94a3b8' }}>{`Volume: ${data.volume.toLocaleString()}`}</p>
        </div>
      );
    }
    return null;
  };

  // Custom dot for signals
  const CustomDot = (props) => {
    const { cx, cy, payload } = props;
    
    // Check if this candle has a signal
    const signal = symbolSignals.find(sig => 
      new Date(sig.signal_time).getTime() === payload.timestamp.getTime()
    );
    
    if (signal) {
      return (
        <circle
          cx={cx}
          cy={cy}
          r={6}
          fill={signal.signal_type === 'BUY' ? '#10b981' : '#ef4444'}
          stroke="#fff"
          strokeWidth={2}
          style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))' }}
        />
      );
    }
    
    return null;
  };

  return (
    <div className="breakout-chart" style={{ width: '100%', height: '400px' }}>
      <div style={{ marginBottom: '1rem' }}>
        <h3 style={{ margin: '0', color: '#f8fafc' }}>{symbol} Intraday Chart</h3>
        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
          <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>
            PDH: <span style={{ color: '#f8fafc', fontWeight: 'bold' }}>₹{pdh.toFixed(2)}</span>
          </span>
          <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>
            PDL: <span style={{ color: '#f8fafc', fontWeight: 'bold' }}>₹{pdl.toFixed(2)}</span>
          </span>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis 
            dataKey="time" 
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
          />
          <YAxis 
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            domain={['dataMin - 1', 'dataMax + 1']}
          />
          <Tooltip content={<CustomTooltip />} />
          
          {/* Previous Day High Line */}
          <ReferenceLine 
            y={pdh} 
            stroke="#10b981" 
            strokeDasharray="5 5" 
            strokeWidth={2}
            label={{ value: "PDH", position: "right", fill: "#10b981" }}
          />
          
          {/* Previous Day Low Line */}
          <ReferenceLine 
            y={pdl} 
            stroke="#ef4444" 
            strokeDasharray="5 5" 
            strokeWidth={2}
            label={{ value: "PDL", position: "right", fill: "#ef4444" }}
          />
          
          {/* Candlestick lines */}
          <Line
            type="monotone"
            dataKey="high"
            stroke="#ef4444"
            strokeWidth={1}
            dot={false}
            name="High"
          />
          <Line
            type="monotone"
            dataKey="low"
            stroke="#3b82f6"
            strokeWidth={1}
            dot={false}
            name="Low"
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke="#f8fafc"
            strokeWidth={2}
            dot={<CustomDot />}
            name="Close"
          />
        </LineChart>
      </ResponsiveContainer>
      
      {/* Signal Legend */}
      {symbolSignals.length > 0 && (
        <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: '#0f172a', borderRadius: '6px' }}>
          <h4 style={{ margin: '0 0 0.5rem 0', color: '#f8fafc', fontSize: '0.875rem' }}>Recent Signals</h4>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            {symbolSignals.slice(-5).map((signal, index) => (
              <div key={index} style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem',
                padding: '0.25rem 0.5rem',
                backgroundColor: signal.signal_type === 'BUY' ? '#10b981' : '#ef4444',
                borderRadius: '4px',
                color: 'white',
                fontSize: '0.75rem'
              }}>
                <span>{signal.signal_type}</span>
                <span>₹{signal.price.toFixed(2)}</span>
                <span>{new Date(signal.signal_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BreakoutChart;
