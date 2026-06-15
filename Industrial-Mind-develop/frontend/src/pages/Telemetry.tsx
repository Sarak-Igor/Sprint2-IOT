import React from 'react';

const Telemetry = () => {
  return (
    <div style={{ padding: '2rem' }}>
      <h2 style={{ color: 'white', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'cyan', boxShadow: '0 0 10px cyan' }}></span>
        Stream de Telemetria em Tempo Real
      </h2>
      <div style={{ 
        background: 'rgba(0,0,0,0.3)', 
        border: '1px solid rgba(255,255,255,0.1)', 
        borderRadius: '12px', 
        padding: '2rem',
        minHeight: '400px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        textAlign: 'center'
      }}>
        <p style={{ color: 'rgba(255,255,255,0.5)', fontStyle: 'italic' }}>
          Aguardando conexão com o servidor de ingestão de dados...
        </p>
      </div>
    </div>
  );
};

export default Telemetry;
