// Quick view: opens a larger photo (front and back where we have it) instead of jumping to email
(function () {
  var cards = document.querySelectorAll('a.pimg.qv');
  if (!cards.length) return;
  var box = document.createElement('div');
  box.className = 'qvbox';
  box.setAttribute('role', 'dialog');
  box.setAttribute('aria-modal', 'true');
  box.hidden = true;
  box.innerHTML = '<div class="qvin"><button type="button" class="qvx" aria-label="Close">&times;</button>' +
    '<div class="qvimg"><img alt=""></div>' +
    '<div class="qvbar"><p class="qvt"></p><a class="btn qvcta" href="#"></a></div></div>';
  document.body.appendChild(box);
  var img = box.querySelector('img'), t = box.querySelector('.qvt'), cta = box.querySelector('.qvcta'), last = null;
  function open(a) {
    last = a;
    img.src = a.getAttribute('data-qv-img');
    img.alt = a.getAttribute('data-qv-title') + ' photos';
    t.textContent = a.getAttribute('data-qv-title');
    cta.textContent = a.getAttribute('data-qv-cta');
    cta.href = a.getAttribute('href');
    box.hidden = false;
    document.documentElement.style.overflow = 'hidden';
    box.querySelector('.qvx').focus();
  }
  function close() {
    box.hidden = true;
    img.src = '';
    document.documentElement.style.overflow = '';
    if (last) last.focus();
  }
  cards.forEach(function (a) {
    a.addEventListener('click', function (e) { e.preventDefault(); open(a); });
    var art = a.closest('article');
    var b = art && art.querySelector('.qvbtn');
    if (b) b.addEventListener('click', function () { open(a); });
  });
  box.addEventListener('click', function (e) { if (e.target === box) close(); });
  box.querySelector('.qvx').addEventListener('click', close);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !box.hidden) close(); });
})();
