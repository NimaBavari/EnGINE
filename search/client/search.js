const SEARCHAPI_BASE_URL = 'localhost:5050';
const MLAPI_BASE_URL = 'localhost:5070';

const searchForm = document.getElementById('searchForm');
const resultsList = document.getElementById('resultsList');

searchForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const searchQuery = document.getElementById('searchInput').value;
    fetch(`${SEARCHAPI_BASE_URL}/search?q=${encodeURIComponent(searchQuery)}`)
        .then((response) => response.json())
        .then((data) => {
            resultsList.innerHTML = '';

            searchForm.className = 'search-form-min';

            let search_query_id = null;
            if ('search_query_id' in data) {
                search_query_id = data.search_query_id
            }

            Object.values(data.pages).forEach((page) => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = page.url;
                a.textContent = page.content.substring(0, 97) + '...';
                a.onclick = () => {
                    if (search_query_id) {
                        fetch(`${MLAPI_BASE_URL}/search-queries/${search_query_id}/visited-urls/`, {
                            method: 'PATCH',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ url: page.url }),
                        });
                    }
                    window.location.href = page.url;
                };
                li.appendChild(a);
                resultsList.appendChild(li);
            });
        })
        .catch((_error) => {
            resultsList.innerHTML = '<li>An error occurred while fetching search results. Please try again later.</li>';
        });
});
