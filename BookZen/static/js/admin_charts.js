
document.addEventListener("DOMContentLoaded", function () {

    // -----------------------------
    // Genre Distribution
    // -----------------------------

    const genreCanvas =
        document.getElementById("genreChart");

    if (genreCanvas) {

        const genreData =
            JSON.parse(
                genreCanvas.dataset.values
            );

        new Chart(
            genreCanvas,
            {
                type: "doughnut",

                data: {
                    labels: Object.keys(genreData),

                    datasets: [{
                        data: Object.values(genreData)
                    }]
                },

                options: {
                    responsive: true,

                    plugins: {
                        legend: {
                            position: "bottom"
                        }
                    }
                }
            }
        );
    }


    // -----------------------------
    // Model Comparison
    // -----------------------------

    const modelCanvas =
        document.getElementById("modelChart");

    if (modelCanvas) {

        new Chart(
            modelCanvas,
            {
                type: "bar",

                data: {

                    labels: [
                        "Naive Bayes",
                        "Logistic Regression",
                        "Linear SVM"
                    ],

                    datasets: [
                        {
                            label: "Accuracy (%)",

                            data: [
                                97.92,
                                100,
                                100
                            ]
                        }
                    ]
                },

                options: {

                    responsive: true,

                    scales: {

                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            }
        );
    }

});
