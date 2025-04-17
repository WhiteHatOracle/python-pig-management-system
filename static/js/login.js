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
  
  