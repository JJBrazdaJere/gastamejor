// Efecto de sombra en la barra superior al hacer scroll.
(function () {
  var topbar = document.getElementById("topbar");
  if (!topbar) return;

  function onScroll() {
    topbar.classList.toggle("scrolled", window.scrollY > 4);
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
})();
