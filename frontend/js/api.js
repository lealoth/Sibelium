console.log('🔗 Inicializando API client...');

function getSessionId() {
  return localStorage.getItem('currentSessionId') || 'default';
}

window.api = {
  chat(message) {
    console.log('📤 Enviando mensaje:', message);
    
    return fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message, session_id: getSessionId()})
    }).then(res => {
      console.log('📥 Respuesta del chat:', res.status);
      if (!res.ok) {
        return res.json().then(err => {
          console.error('❌ Error en respuesta:', err);
          throw new Error(err.detail || 'API error');
        });
      }
      return res.json();
    });
  },
  getState() {
    return fetch('/api/state?session_id=' + getSessionId()).then(res => res.json());
  },
  getHistory() {
    return fetch('/api/history?session_id=' + getSessionId()).then(res => res.json());
  },
  getThoughts() {
    return fetch('/api/thoughts/last?session_id=' + getSessionId()).then(res => res.json());
  },
  reset() {
    return fetch('/api/reset?session_id=' + getSessionId(), { method: 'POST' }).then(res => res.json());
  },
};

console.log('✅ API client inicializado');