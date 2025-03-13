// Dark/Light Mode Toggle
document.querySelector('.theme-toggle').addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
  });
  
  // Mobile Navigation
  document.querySelector('.hamburger').addEventListener('click', () => {
    document.querySelector('.nav-links').classList.toggle('active');
  });
  
  // Scroll Animationen
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = 1;
        entry.target.style.transform = 'translateY(0)';
      }
    });
  });
  
  document.querySelectorAll('.fade-in, .slide-up').forEach((el) => {
    observer.observe(el);
  });

function scrollTo(element){
    document.getElementById(element).scrollIntoView()
}

// Banner schließen
document.getElementById('close-banner').addEventListener('click', () => {
  document.getElementById('news-banner').style.display = 'none';
});

// Optional: Banner nach einiger Zeit automatisch schließen
setTimeout(() => {
  document.getElementById('news-banner').style.display = 'none';
}, 10000); // Schließt das Banner nach 10 Sekunden


