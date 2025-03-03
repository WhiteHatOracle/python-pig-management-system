document.addEventListener("DOMContentLoaded", () => {
    const track = document.querySelector(".carousel__track");
    const slides = Array.from(track.children);
    const nextButton = document.querySelector(".next");
    const prevButton = document.querySelector(".prev");

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

    // Move to next slide
    nextButton.addEventListener("click", () => {
        const currentSlide = track.querySelector(".current-slide");

        const nextSlide = currentSlide.nextElementSibling || slides[0]; // Loop to first slide

        moveToSlide(track, currentSlide, nextSlide);
    });

    // Move to previous slide
    prevButton.addEventListener("click", () => {
        const currentSlide = track.querySelector(".current-slide");

        const prevSlide = currentSlide.previousElementSibling || slides[slides.length - 1]; // Loop to last slide

        moveToSlide(track, currentSlide, prevSlide);
    });

    // Recalculate slide positions if window resizes
    window.addEventListener("resize", () => {
        slideWidth = slides[0].getBoundingClientRect().width;
        slides.forEach(setSlidePosition);
    });
});
