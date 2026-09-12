document.addEventListener("DOMContentLoaded", function () {

    const savedTheme = localStorage.getItem("bookzen-theme");

    if (savedTheme) {
        document.documentElement.setAttribute(
            "data-theme",
            savedTheme
        );
    } else {
        document.documentElement.setAttribute(
            "data-theme",
            "dark"
        );
    }

    const toggleButton =
        document.getElementById("themeToggle");

    if (toggleButton) {

        updateButton();

        toggleButton.addEventListener(
            "click",
            function () {

                const currentTheme =
                    document.documentElement.getAttribute(
                        "data-theme"
                    );

                const newTheme =
                    currentTheme === "dark"
                        ? "light"
                        : "dark";

                document.documentElement.setAttribute(
                    "data-theme",
                    newTheme
                );

                localStorage.setItem(
                    "bookzen-theme",
                    newTheme
                );

                updateButton();
            }
        );
    }


    function updateButton() {

        const currentTheme =
            document.documentElement.getAttribute(
                "data-theme"
            );

        if (currentTheme === "dark") {

            toggleButton.innerHTML =
                "☀️ Light";

        } else {

            toggleButton.innerHTML =
                "🌙 Dark";
        }
    }

});
