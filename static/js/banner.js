document.addEventListener('DOMContentLoaded', function(){
  const socket = io();
  const levelEl = document.getElementById('bandeau-level');
  const msgEl = document.getElementById('bandeau-message');

  socket.on('connect', () => {
    socket.emit('request_banner');
  });

  socket.on('banner_update', (data) => {
    if (!data) return;
    const level = data.level || 'Info';
    const message = data.message || '';
    levelEl.textContent = level;
    msgEl.textContent = message;

    // Visual changes for Code Rouge
    const banner = document.getElementById('bandeau');
    banner.classList.remove('code-vert','code-orange','code-rouge');
    if (level.toLowerCase().includes('rouge') || level.toLowerCase().includes('code rouge')) {
      banner.classList.add('code-rouge');
      document.body.classList.add('alert-red');
      // optional: play sound (ask user permission)
    } else {
      document.body.classList.remove('alert-red');
    }
  });
});
