(function(){
  function clock(){
    var d=new Date();
    var h=('0'+d.getHours()).slice(-2), m=('0'+d.getMinutes()).slice(-2), s=('0'+d.getSeconds()).slice(-2);
    document.getElementById('clock').textContent=h+':'+m+':'+s;
  }
  setInterval(clock,1000); clock();

  var form = document.getElementById('installForm');
  var log = document.getElementById('log');

  form.addEventListener('submit', function(e){
    e.preventDefault();
    log.textContent = 'Отправка конфигурации...\n';
    var btn = form.querySelector('button');
    btn.disabled = true;

    var data = {
      root: document.getElementById('root').value,
      basePort: parseInt(document.getElementById('basePort').value),
      agentCount: parseInt(document.getElementById('agentCount').value),
      chatPort: parseInt(document.getElementById('chatPort').value),
      proxyPort: parseInt(document.getElementById('proxyPort').value)
    };

    fetch('/api/install', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    }).then(r => r.json()).then(res => {
      if(res.ok) {
        log.textContent += 'Установка запущена успешно.\n' + (res.log || '');
        var a = document.createElement('a');
        a.href = 'http://127.0.0.1:' + data.chatPort + '/';
        a.target = '_blank';
        a.className = 'pbtn';
        a.style.display = 'block';
        a.style.textAlign = 'center';
        a.style.marginTop = '15px';
        a.style.textDecoration = 'none';
        a.textContent = 'ПЕРЕЙТИ В МЕЙНФРЕЙМ';
        form.appendChild(a);
        form.style.display = 'none';
      } else {
        log.textContent += 'Ошибка: ' + (res.error || 'unknown') + '\n';
        btn.disabled = false;
      }
    }).catch(err => {
      log.textContent += 'Сетевая ошибка: ' + err + '\n';
      btn.disabled = false;
    });
  });
})();