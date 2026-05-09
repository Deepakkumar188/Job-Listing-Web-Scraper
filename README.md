# Job-Listing-Web-Scraper

A beginner-friendly Python web scraper that extracts job listing data from a
live website and saves it to a structured CSV file.

---

## 🗂️ Project Structure

```
job_scraper/
├── scraper.py          # Main scraper (fetch → parse → save)
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── output/             # Generated CSV files land here
└── logs/               # Run logs land here
```

---

## ⚡ Quick Start

### 1 · Clone / download the project

```bash
git clone <your-repo-url>
cd job_scraper
```

### 2 · Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows
```

### 3 · Install dependencies

```bash
pip install -r requirements.txt
```

### 4 · Run the scraper

```bash
python scraper.py
```

The results are saved to **`output/job_listings.csv`** and a run log is written
to **`logs/scraper.log`**.

---

## 🔍 How It Works

| Step | What happens |
|------|--------------|
| **Fetch** | `requests.get()` downloads the HTML page with a realistic User-Agent header and automatic retry logic (up to 3 attempts, exponential back-off). |
| **Parse** | `BeautifulSoup` walks the DOM and extracts *Job Title*, *Company Name*, and *Location* from every job card. |
| **Save** | `pandas` assembles the records into a DataFrame and exports them to CSV with today's date stamped in a *Scraped Date* column. |

### Target site

`https://realpython.github.io/fake-jobs/` — a purpose-built scraping sandbox
maintained by Real Python. It is safe and legal to scrape.

---

## 📄 Sample Output (`output/job_listings.csv`)

```
Job Title,Company Name,Location,Scraped Date
Senior Python Developer,Payne, Roberts and Davis,"Stewartbury, AA",2025-05-09
Energy engineer,Vasquez-Davidson,"Christopherville, AA",2025-05-09
Legal executive,Jackson, Chambers and Levy,"Port Ericaburgh, AA",2025-05-09
…
```

---

## 🛡️ Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Network timeout | Retried up to 3× with exponential back-off |
| HTTP 4xx / 5xx | Logged and retried |
| Missing HTML field | That card is skipped; rest of page is saved |
| No cards found | Warning logged; empty CSV not written |

---

## 🛠️ Technologies

- **Python 3.10+**
- **requests** – HTTP client
- **BeautifulSoup4** – HTML parser
- **pandas** – data wrangling & CSV export
- **logging** – structured run logs

---

## 📌 Extending the Scraper

- **Multiple pages** – wrap `fetch_page` + `parse_jobs` in a loop over paginated URLs.
- **Different site** – update `BASE_URL` and the CSS selectors in `parse_jobs`.
- **Scheduled runs** – use `cron` (Linux/macOS) or Task Scheduler (Windows) to
  run `scraper.py` daily and append results to the CSV.

---

## ⚖️ Legal & Ethical Use

Always check a site's `robots.txt` and Terms of Service before scraping it in
production. This project targets a sandbox site explicitly designed for learning.
