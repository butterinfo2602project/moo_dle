function setupDigitInputs() {
    const inputs = Array.from(document.querySelectorAll(".digit-input"));

    // if not on the game page, stop
    if (inputs.length === 0) return;

    inputs.forEach((input, index) => {
        input.addEventListener("input", function () {
            // only keep 1 number
            this.value = this.value.replace(/\D/g, "").slice(0, 1);

            // move to next box automatically
            if (this.value.length === 1 && index < inputs.length - 1) {
                inputs[index + 1].focus();
                inputs[index + 1].select();
            }
        });

        input.addEventListener("keydown", function (event) {
            // go back if backspace on empty box
            if (event.key === "Backspace" && this.value === "" && index > 0) {
                inputs[index - 1].focus();
            }

            // allow left/right arrow movement
            if (event.key === "ArrowLeft" && index > 0) {
                inputs[index - 1].focus();
            }

            if (event.key === "ArrowRight" && index < inputs.length - 1) {
                inputs[index + 1].focus();
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", function () {
    setupDigitInputs();
});