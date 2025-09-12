# EnGINE

Simple web search and analytics system.

## Key Features

### Search

* Minimalist user interface for streamlined web searches
* Enables document searches within the distributed storage system
* Retrieves search results in a prioritized manner, leveraging an advanced ranking algorithm
* Employs multi-threaded web crawling techniques complemented by caching mechanisms and cache validation strategies
* Supports text retrieval from documents using an inverted index database for efficient search capabilities.

### Saerch Analytics

* Content-based recommender system
* Implements a simple data pipeline that gathers user profiles, search queries, and clicked URLs, uses this data to train the neural network, performs predictions, and stores the results in adaptable storage for prioritising user search rankings.

## Usage

### Spin Up

Run:

```sh
make start
```

to spin up the whole application.

### Linting and Formatting

Run:

```sh
make cleanup
```

to run linting and formatting.

### Set Up Dev Environment

Run:

```sh
make set_dev_env
```

to set up the dev environment.

This sets:
- git pre-commit hook

### Testing

Run:

```sh
make test
```

to start the tests

## Tools and Techniques Used

Tools:

* Python: Primary programming language, used for implementing various components including microservices, machine learning components, and REST APIs
* JavaScript: Minimal usage, namely, for the search user interface
* PostgreSQL: Used as the relational database
* Redis: Used for caching and key-value storage
* Elasticsearch: Used for search functionality, utilising advanced inverted index database capabilities
* Docker: Used for containerization, facilitating deployment and scalability of microservices
* Shell scripting: Used for automation tasks and deployment scripts.
* AWS: Used for hosting services, storage, and for utilizing managed services like Elasticsearch.

Architecture and Concepts:

* Microservices (non-event-driven): A distributed architecture with 5 independent deployable services
* Smart caching: Implemented for optimizing data access and performance
* Multi-threaded crawler: Utilized for concurrent data collection and web scraping
* Machine learning (very simple recommender system): Basic implementation of ML for providing recommendations and its integration to the system
* REST APIs and HTTP transport: Used for communication between microservices
* Very simple data pipeline: Implemented for processing and moving data between components using simple data processing workflows.
