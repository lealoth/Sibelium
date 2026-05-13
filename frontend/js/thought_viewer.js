window.thoughtViewer = {
  render(thoughts) {
    const panel = document.getElementById('thought-panel');
    if (!panel) return;
    
    panel.innerHTML = '';
    
    if (!thoughts || thoughts.length === 0) {
      panel.innerHTML = '<div class="thought-item"><p>Sin pensamientos aún...</p></div>';
      return;
    }
    
    thoughts.forEach((item) => {
      const div = document.createElement('div');
      div.className = 'thought-item';
      const phase = item.phase || 'Pensamiento';
      const thought = item.generated_thought || item.thought || '...';
      div.innerHTML = `<strong>${phase}</strong><p>${thought}</p>`;
      panel.appendChild(div);
    });
    
    panel.scrollTop = panel.scrollHeight;
  },
  
  clear() {
    const panel = document.getElementById('thought-panel');
    if (panel) panel.innerHTML = '';
  }
};