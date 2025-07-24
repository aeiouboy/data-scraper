# Adaptive Scraping System - Implementation

This document outlines the design and implementation of an Adaptive Scraping System. The goal of this system is to create a resilient, self-monitoring scraping process that can detect and react to website changes, minimizing downtime and manual intervention.

## Core Concepts

The system is built around a continuous feedback loop:

1.  **Execute:** Run scraping jobs as normal.
2.  **Monitor:** Continuously monitor the performance and success rates of these jobs.
3.  **Analyze:** Analyze the results to detect anomalies, such as a sudden spike in failures for a specific retailer.
4.  **Adapt:** Take automated actions based on the analysis, such as adjusting parameters, pausing jobs, or notifying developers.

## System Components

This system introduces several new logical components that work with the existing architecture:

-   **Scraping Executor:** The existing system that runs scrape jobs (FastAPI, Scraping Manager, Scraper Adapters).
-   **Job Monitor:** A background service that periodically checks the `scrape_jobs` table in the database for completed or failed jobs.
-   **Performance Analyzer:** A service that ingests data from the Job Monitor and calculates key performance indicators (KPIs) for each scraper, such as success rate, average runtime, and common error types.
-   **Change Detector:** The core of the adaptive system. It compares current performance metrics against historical benchmarks to detect statistically significant deviations that indicate a website change.
-   **Adaptation Manager:** This component is triggered by the Change Detector and decides on the appropriate course of action.
-   **Notification Service:** A service for sending alerts (e.g., via email, Slack, or another messaging platform).

## Adaptive Scraping Flow

The following diagram illustrates the complete, continuous flow of the Adaptive Scraping System.

```mermaid
graph TD
    subgraph Core Scraping Execution
        A[Scraping Executor] -- Writes Job Status --> B[Supabase DB: scrape_jobs]
    end

    subgraph Adaptive Feedback Loop
        C[1. Job Monitor] -- Periodically Polls --> B
        C -- Sends Job Results --> D[2. Performance Analyzer]
        D -- Calculates KPIs (Success Rate, etc.) --> E[3. Change Detector]
        E -- Compares to Benchmarks --> F{Anomaly Detected?}
        F -- Yes --> G[4. Adaptation Manager]
        F -- No --> C
    end

    subgraph Automated Actions
        G -- Takes Action --> H[Pause Jobs for Retailer]
        G -- Takes Action --> I[Adjust Scraping Parameters]
        G -- Takes Action --> J[Send Developer Alert]
        G -- Takes Action --> K[Queue for AI Re-Analysis (Future)]
    end

    J -- via --> L[Notification Service]
    I -- Updates Config --> A
```

## Detailed Step-by-Step Flow

This flow operates as a continuous, automated loop.

1.  **Scraping Execution:**
    *   The `Scraping Executor` runs jobs as requested by the user or a schedule.
    *   As jobs are completed, their final status (`completed`, `failed`), along with statistics (`success_items`, `failed_items`), is written to the `scrape_jobs` table in the Supabase database.

2.  **Job Monitoring (Continuous):**
    *   The `Job Monitor` service runs in the background, periodically querying the `scrape_jobs` table for recently completed jobs.

3.  **Performance Analysis:**
    *   The results of these jobs are passed to the `Performance Analyzer`.
    *   The analyzer aggregates the data for each retailer (e.g., HomePro, ThaiWatsadu) and calculates key metrics, such as the success rate over the last 24 hours, the average number of items scraped, and the most common error messages.

4.  **Change Detection:**
    *   The `Change Detector` takes these fresh KPIs and compares them to historical benchmarks for that same retailer.
    *   **Example:** If the success rate for the `HomeProScraper` is normally 98%, but it suddenly drops to 20% over the last hour, the detector flags this as a critical anomaly.

5.  **Adaptation and Action:**
    *   When the `Change Detector` flags an anomaly, it triggers the `Adaptation Manager`.
    *   The `Adaptation Manager` evaluates the severity and type of the anomaly and decides on one or more actions:
        *   **Immediate Action (High Severity):** If the failure rate is catastrophic (e.g., > 90%), it can automatically **pause all new scraping jobs** for that retailer to prevent wasting resources.
        *   **Parameter Adjustment:** If performance has degraded but not failed completely, it could attempt to **adjust scraping parameters**, such as increasing the rate-limit delay or switching to a different type of proxy.
        *   **Alerting:** For any significant failure, it will use the `Notification Service` to **send a detailed alert** to the development team, flagging the likely issue.
        *   **Future AI Re-Analysis:** In a more advanced implementation, it could add the retailer's website to a queue for an **AI-powered analysis**. This AI would attempt to re-learn the website's new structure and suggest changes to the scraper code.

6.  **Loop Continuation:**
    *   If no anomaly is detected, the loop continues, with the `Job Monitor` continuing to poll for new job results.

This adaptive system transforms the scraping process from a brittle, manual one into a resilient, automated one that is far more robust to changes in the target websites.
