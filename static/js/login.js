document.addEventListener("DOMContentLoaded", () => {
    const track = document.querySelector(".carousel__track");
    const slides = Array.from(track.children);
    const nextButton = document.querySelector(".next");
    const prevButton = document.querySelector(".prev");
    const dotsNav = document.querySelector(".carousel__nav");
    const dots = Array.from(dotsNav.children);

    let slideWidth = slides[0].getBoundingClientRect().width; // Get slide width

    // Arrange slides next to each other
    const setSlidePosition = (slide, index) => {
        slide.style.left = `${slideWidth * index}px`;
    };
    slides.forEach(setSlidePosition);

    const moveToSlide = (track, currentSlide, targetSlide) => {
        track.style.transform = `translateX(-${targetSlide.style.left})`;
        currentSlide.classList.remove("current-slide");
        targetSlide.classList.add("current-slide");
    };

    const updateDots = (currentDot, targetDot) => {
        currentDot.classList.remove("current-slide");
        targetDot.classList.add("current-slide");
    };

    // Move to next slide
    nextButton.addEventListener("click", () => {
        const currentSlide = track.querySelector(".current-slide");
        const currentDot = dotsNav.querySelector(".current-slide");

        const nextSlide = currentSlide.nextElementSibling || slides[0]; // Loop to first slide
        const nextDot = currentDot.nextElementSibling || dots[0];

        moveToSlide(track, currentSlide, nextSlide);
        updateDots(currentDot, nextDot);
    });

    // Move to previous slide
    prevButton.addEventListener("click", () => {
        const currentSlide = track.querySelector(".current-slide");
        const currentDot = dotsNav.querySelector(".current-slide");

        const prevSlide = currentSlide.previousElementSibling || slides[slides.length - 1]; // Loop to last slide
        const prevDot = currentDot.previousElementSibling || dots[dots.length - 1];

        moveToSlide(track, currentSlide, prevSlide);
        updateDots(currentDot, prevDot);
    });

    // Click on navigation dots
    dotsNav.addEventListener("click", (e) => {
        const targetDot = e.target;
        if (!dots.includes(targetDot)) return; // Ignore clicks outside buttons

        const currentSlide = track.querySelector(".current-slide");
        const currentDot = dotsNav.querySelector(".current-slide");

        const targetIndex = dots.findIndex((dot) => dot === targetDot);
        const targetSlide = slides[targetIndex];

        moveToSlide(track, currentSlide, targetSlide);
        updateDots(currentDot, targetDot);
    });

    // Recalculate slide positions if window resizes
    window.addEventListener("resize", () => {
        slideWidth = slides[0].getBoundingClientRect().width;
        slides.forEach(setSlidePosition);
    });
});

/* script.js */
/* script.js */
document.addEventListener('DOMContentLoaded', () => {
    const features = document.querySelectorAll('.feature');
    features.forEach((el, index) => {
      el.style.animationDelay = `${0.3 * index}s`;
    });
  
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    }, { threshold: 0.1 });
  
    document.querySelectorAll('.section-scroll').forEach(section => {
      observer.observe(section);
    });
  
    const hamburger = document.getElementById('hamburger');
    const mobileMenu = document.getElementById('mobileMenu');
    let isMenuOpen = false;
  
    hamburger.addEventListener('click', () => {
      isMenuOpen = !isMenuOpen;
      mobileMenu.classList.toggle('show');
      hamburger.classList.toggle('open');
    });
  
    document.addEventListener('click', (e) => {
      if (isMenuOpen && !mobileMenu.contains(e.target) && e.target !== hamburger) {
        mobileMenu.classList.remove('show');
        hamburger.classList.remove('open');
        isMenuOpen = false;
      }
    });
  
    window.addEventListener('scroll', () => {
      if (isMenuOpen) {
        mobileMenu.classList.remove('show');
        hamburger.classList.remove('open');
        isMenuOpen = false;
      }
    });
  });
  
  // New Code Here
  document.addEventListener('DOMContentLoaded', function() {
  
  // --- Mobile Navigation ---
  const navToggle = document.getElementById('nav-toggle');
  const nav = document.getElementById('main-nav');
  // NOTE: You'll need to add a mobile navigation pane to your HTML
  // to make this fully functional, similar to your original design.
  if (navToggle) {
    navToggle.addEventListener('click', function() {
      // Logic to show/hide mobile nav
      alert('Mobile nav toggle clicked! Implement your mobile menu logic here.');
    });
  }

  // --- Dark Mode Toggle ---
  const themeToggle = document.getElementById('theme-toggle');
  const body = document.body;

  // Function to apply the saved theme
  const applyTheme = (theme) => {
    if (theme === 'dark') {
      body.classList.add('dark-mode');
    } else {
      body.classList.remove('dark-mode');
    }
  };

  // Check for saved theme in localStorage
  const savedTheme = localStorage.getItem('theme');
  
  // Check for system preference if no theme is saved
  if (!savedTheme && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      applyTheme('dark');
  } else {
      applyTheme(savedTheme || 'light');
  }


  themeToggle.addEventListener('click', () => {
    if (body.classList.contains('dark-mode')) {
      body.classList.remove('dark-mode');
      localStorage.setItem('theme', 'light');
    } else {
      body.classList.add('dark-mode');
      localStorage.setItem('theme', 'dark');
    }
  });

});