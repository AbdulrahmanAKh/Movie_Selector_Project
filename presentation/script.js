// CineVault Interactive Web Application Engine

const initialMovies = [
    {
        id: 'interstellar',
        title: 'Interstellar',
        genre: 'Sci-Fi',
        year: 2014,
        rating: 8.7,
        poster: 'movie_posters/interstellar.jpg',
        director: 'Christopher Nolan',
        description: 'When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot, Joseph Cooper, is tasked to pilot a spacecraft, along with a team of researchers, to find a new planet for humans.',
        user: 'A. Alkhatib'
    },
    {
        id: 'inception',
        title: 'Inception',
        genre: 'Sci-Fi',
        year: 2010,
        rating: 8.8,
        poster: 'movie_posters/inception.jpg',
        director: 'Christopher Nolan',
        description: 'A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O., but his tragic past may doom the project.',
        user: 'A. Alkhatib'
    },
    {
        id: 'breakingbad',
        title: 'Breaking Bad',
        genre: 'Crime',
        year: 2008,
        rating: 9.5,
        poster: 'movie_posters/breakingbad.jpg',
        director: 'Vince Gilligan',
        description: 'A chemistry teacher diagnosed with inoperable lung cancer turns to manufacturing and selling methamphetamine with a former student in order to secure his family\'s financial future.',
        user: 'A. Alkhatib'
    },
    {
        id: 'oppenheimer',
        title: 'Oppenheimer',
        genre: 'Biography',
        year: 2023,
        rating: 8.9,
        poster: 'movie_posters/oppenheimer.jpg',
        director: 'Christopher Nolan',
        description: 'The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb during World War II.',
        user: 'A. Alkhatib'
    },
    {
        id: 'joker',
        title: 'Joker',
        genre: 'Drama',
        year: 2019,
        rating: 8.4,
        poster: 'movie_posters/joker.jpg',
        director: 'Todd Phillips',
        description: 'During the 1980s, a failed stand-up comedian is driven insane and turns to a life of crime and chaos in Gotham City while becoming an infamous psychopathic crime figure.',
        user: 'A. Alkhatib'
    },
    {
        id: 'thewolfofstreet',
        title: 'The Wolf of Wall Street',
        genre: 'Biography',
        year: 2013,
        rating: 8.2,
        poster: 'movie_posters/thewolfofstreet.jpg',
        director: 'Martin Scorsese',
        description: 'Based on the true story of Jordan Belfort, from his rise to a wealthy stock-broker living the high life to his fall involving crime, corruption and the federal government.',
        user: 'A. Alkhatib'
    }
];

let movies = [...initialMovies];
let activeProfile = 'A. Alkhatib';

// DOM Elements
const moviesGrid = document.getElementById('moviesGrid');
const searchInput = document.getElementById('searchInput');
const genreFilter = document.getElementById('genreFilter');
const sortFilter = document.getElementById('sortFilter');
const movieModal = document.getElementById('movieModal');
const modalBody = document.getElementById('modalBody');
const addModal = document.getElementById('addModal');
const addMovieBtn = document.getElementById('addMovieBtn');

// Initial Render
renderMovies();

// Event Listeners
if (searchInput) searchInput.addEventListener('input', renderMovies);
if (genreFilter) genreFilter.addEventListener('change', renderMovies);
if (sortFilter) sortFilter.addEventListener('change', renderMovies);
if (addMovieBtn) addMovieBtn.addEventListener('click', openAddModal);

function renderMovies() {
    if (!moviesGrid) return;

    let filtered = [...movies];
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const selectedGenre = genreFilter ? genreFilter.value : 'all';
    const selectedSort = sortFilter ? sortFilter.value : 'rating-desc';

    // Search filter
    if (query) {
        filtered = filtered.filter(m =>
            m.title.toLowerCase().includes(query) ||
            (m.director && m.director.toLowerCase().includes(query)) ||
            m.genre.toLowerCase().includes(query)
        );
    }

    // Genre filter
    if (selectedGenre !== 'all') {
        filtered = filtered.filter(m => m.genre.toLowerCase() === selectedGenre.toLowerCase());
    }

    // Sorting
    filtered.sort((a, b) => {
        if (selectedSort === 'rating-desc') return b.rating - a.rating;
        if (selectedSort === 'year-desc') return b.year - a.year;
        if (selectedSort === 'year-asc') return a.year - b.year;
        if (selectedSort === 'title-asc') return a.title.localeCompare(b.title);
        return 0;
    });

    if (filtered.length === 0) {
        moviesGrid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: #777;">
                <p style="font-size: 18px; margin-bottom: 8px;">No movies found matching your filter</p>
                <button class="btn btn-outline" onclick="resetFilters()">Reset Filters</button>
            </div>
        `;
        return;
    }

    moviesGrid.innerHTML = filtered.map(movie => `
        <div class="movie-card" onclick="openMovieModal('${movie.id}')">
            <div class="card-poster-wrap">
                <img src="${movie.poster}" alt="${movie.title}" class="card-poster" onerror="this.src='movie_posters/inception.jpg'">
                <div class="card-play-overlay">
                    <div class="play-circle">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <polygon points="5 3 19 12 5 21 5 3"></polygon>
                        </svg>
                    </div>
                </div>
            </div>
            <div class="card-details">
                <h3 class="card-title">${movie.title}</h3>
                <div class="card-meta">
                    <span style="color: #46d369; font-weight: 700;">★ ${movie.rating}</span>
                    <span>${movie.year}</span>
                </div>
                <span class="card-genre">${movie.genre}</span>
            </div>
        </div>
    `).join('');
}

function resetFilters() {
    if (searchInput) searchInput.value = '';
    if (genreFilter) genreFilter.value = 'all';
    if (sortFilter) sortFilter.value = 'rating-desc';
    renderMovies();
}

function selectProfile(profileId, name, letter) {
    activeProfile = profileId;
    document.querySelectorAll('.profile-card').forEach(card => card.classList.remove('active'));
    const targetCard = document.querySelector(`[data-profile="${profileId}"]`);
    if (targetCard) targetCard.classList.add('active');

    const navName = document.getElementById('navProfileName');
    const navAvatar = document.getElementById('navAvatar');
    if (navName) navName.textContent = name;
    if (navAvatar) navAvatar.textContent = letter;

    const subtitle = document.getElementById('collectionSubtitle');
    if (subtitle) subtitle.textContent = `Viewing ${name}'s personalized movie collection.`;
}

function openMovieModal(movieId) {
    const movie = movies.find(m => m.id === movieId);
    if (!movie || !modalBody || !movieModal) return;

    modalBody.innerHTML = `
        <div style="display: flex; gap: 24px; flex-wrap: wrap;">
            <img src="${movie.poster}" alt="${movie.title}" style="width: 200px; height: 300px; object-fit: cover; border-radius: 8px;">
            <div style="flex: 1; min-width: 260px;">
                <h2 style="font-size: 28px; font-weight: 800; margin-bottom: 8px; color: white;">${movie.title}</h2>
                <div style="display: flex; gap: 14px; align-items: center; font-size: 14px; margin-bottom: 16px;">
                    <span style="color: #46d369; font-weight: bold;">★ ${movie.rating} / 10</span>
                    <span style="color: #aaa;">${movie.year}</span>
                    <span style="background: rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 4px;">${movie.genre}</span>
                </div>
                <p style="color: #bbb; font-size: 14px; line-height: 1.6; margin-bottom: 20px;">${movie.description}</p>
                <p style="font-size: 13px; color: #888; margin-bottom: 20px;"><strong>Director:</strong> ${movie.director || 'N/A'}</p>
                <div style="display: flex; gap: 10px;">
                    <a href="https://github.com/AbdulrahmanAKh/Movie_Selector_Project" class="btn btn-primary">
                        View PyQt5 Code
                    </a>
                    <button class="btn btn-outline" onclick="deleteMovie('${movie.id}')">
                        Remove from Library
                    </button>
                </div>
            </div>
        </div>
    `;

    movieModal.classList.add('active');
}

function closeMovieModal() {
    if (movieModal) movieModal.classList.remove('active');
}

function openAddModal() {
    if (addModal) addModal.classList.add('active');
}

function closeAddModal() {
    if (addModal) addModal.classList.remove('active');
}

function handleNewMovie(e) {
    e.preventDefault();
    const title = document.getElementById('newTitle').value;
    const genre = document.getElementById('newGenre').value;
    const year = parseInt(document.getElementById('newYear').value) || 2024;
    const rating = parseFloat(document.getElementById('newRating').value) || 8.0;

    const newMovie = {
        id: 'custom-' + Date.now(),
        title,
        genre,
        year,
        rating,
        poster: 'movie_posters/inception.jpg',
        director: 'Self-Added',
        description: `Custom movie entry added directly to the active collection.`,
        user: activeProfile
    };

    movies.unshift(newMovie);
    closeAddModal();
    renderMovies();
    document.getElementById('addMovieForm').reset();
}

function deleteMovie(id) {
    movies = movies.filter(m => m.id !== id);
    closeMovieModal();
    renderMovies();
}
