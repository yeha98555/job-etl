# LinkedIn Job Scraper

Scrape job data from LinkedIn and return as JSON.
```sh
docker build -t linkedin-job-scraper .
docker run -p 8080:8080 linkedin-job-scraper
```

Navigate to `http://localhost:8080/<location>/<time_range>` to see the result.

For example: `http://localhost:8080/scrape/taiwan/r86400`
