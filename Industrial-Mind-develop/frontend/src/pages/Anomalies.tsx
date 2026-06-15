import React from 'react';
import { ExpandableCard } from '@sarak/lib-ui-core';

const Anomalies = () => {
  return (
    <div style={{ padding: '2rem' }}>
      <ExpandableCard title="Log de Anomalias" status="online">
        <div style={{ padding: '1rem', background: 'rgba(255, 100, 100, 0.1)', borderRadius: '8px', border: '1px solid rgba(255, 100, 100, 0.2)' }}>
          <p style={{ color: '#ff6666', fontWeight: 'bold' }}>NENHUMA ANOMALIA CRÍTICA</p>
          <p style={{ opacity: 0.7, fontSize: '0.9rem' }}>Os sensores de vibração e temperatura estão operando dentro dos limites nominais.</p>
        </div>
      </ExpandableCard>
    </div>
  );
};

export default Anomalies;
