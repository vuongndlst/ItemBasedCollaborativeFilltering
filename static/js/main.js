document.getElementById("recommendation-form").addEventListener("submit", async function (e) {
    e.preventDefault();

    const userId = document.getElementById("user_id").value;
    const movieTitle = document.getElementById("movie_title").value;

    const response = await fetch("/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ user_id: userId, movie_title: movieTitle }),
    });

    const recommendations = await response.json();
    const recommendationsDiv = document.getElementById("recommendations");
    recommendationsDiv.innerHTML = "";

    if (recommendations.error) {
        recommendationsDiv.innerHTML = `<div class="alert alert-danger">${recommendations.error}</div>`;
        return;
    }

    recommendations.forEach((rec, index) => {
        if (index % 6 === 0) {
            const row = document.createElement("div");
            row.className = "row mb-4";
            recommendationsDiv.appendChild(row);
        }

        const card = `
            <div class="col-md-2">
                <div class="card h-100 hover-blur">
                    <img src="${rec.poster_url || '/static/images/default-poster.jpg'}" class="card-img-top" alt="Poster">
                    <div class="card-body d-flex flex-column">
                        <h5 class="card-title text-truncate">${rec.title}</h5>
                        <p class="card-text text-truncate">${rec.description}</p>
                        <p class="card-text"><strong>Predicted Rating:</strong> ${rec.predicted_rating}</p>
                        <div class="mt-auto">
                            <a href="${rec.imdb_link}" target="_blank" class="btn btn-primary btn-sm">IMDB</a>
                            <a href="${rec.tmdb_link}" target="_blank" class="btn btn-secondary btn-sm">TMDB</a>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const currentRow = recommendationsDiv.lastElementChild;
        currentRow.innerHTML += card;
    });
});
