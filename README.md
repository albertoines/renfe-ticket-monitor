# 🤖 Renfe Ticket Monitor with Python and Selenium

[![Renfe Ticket Monitor](https://github.com/albertoines/renfe-ticket-monitor/actions/workflows/main.yml/badge.svg)](https://github.com/albertoines/renfe-ticket-monitor/actions/workflows/main.yml)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)

This project is an advanced web scraping script that automatically monitors Renfe.com for available train tickets. When a specific train, previously marked as "Full", has seats available, the script sends an email notification.

The system is designed to run autonomously on a schedule in the cloud using **GitHub Actions**, eliminating the need for a dedicated server or keeping a personal computer running 24/7.

---

### 🎥 Live Demo (Local Execution)

*(This is the most important part of your portfolio. Record a GIF of the script running locally and replace the placeholder below. It's a powerful way to show your work in action!)*

![GIF demonstration of the script in action](https://raw.githubusercontent.com/albertoines/renfe-ticket-monitor/refs/heads/main/demo/Renfe_ticket_monitor_demo.gif)

---

### ✨ Key Features

*   **Full Automation:** Fills the search form (origin, destination, date) by mimicking human behavior.
*   **Complex UI Handling:** Overcomes challenges of the Renfe website, including dynamic calendar widgets that do not accept `send_keys()`.
*   **Intelligent Availability Check:** Determines if a train has available seats based on the presence of a price element, rather than relying on fragile text like "Train Full".
*   **Email Notifications:** Sends a clear and concise email alert the moment tickets are found, enabling a quick purchase.
*   **Cloud-Scheduled Execution:** Uses a **GitHub Actions** workflow to run at regular intervals (e.g., every 15 minutes) completely free of charge and serverless.
*   **Robust Error Handling:** Implements explicit waits (`WebDriverWait`), exception handling, and automatically generates screenshots upon failure to facilitate debugging.
*   **Secure Configuration:** Leverages **GitHub Secrets** to securely store email credentials, keeping them out of the source code.

---

### 🛠️ Tech Stack

*   **Language:** Python 3
*   **Web Scraping & Automation:** Selenium
*   **Driver Management:** Webdriver-manager
*   **CI/CD & Scheduled Execution:** GitHub Actions
*   **Python Standard Libraries:** `smtplib`, `ssl`, `os`, `datetime`

---

### 🧠 Technical Challenges & Solutions

This project presented several interesting technical challenges typical of modern web scraping:

1.  **Autocomplete Search Form:**
    *   **Challenge:** The Origin and Destination fields load suggestions dynamically. Interacting with them too quickly causes race condition errors.
    *   **Solution:** A strategic 1-second pause was implemented after `send_keys()` to allow the page's JavaScript to process the input and render the suggestions before the script attempts to click on one.

2.  **Complex Calendar Widget:**
    *   **Challenge:** The calendar is not a simple `input`. It requires a specific sequence of clicks: open, switch to "One-way", navigate through months, and finally select a day. Furthermore, the calendar identifies days using a `data-time` attribute (a Unix timestamp) instead of a simple ID.
    *   **Solution:** A workflow was designed to replicate the user's journey exactly. The script calculates the precise Unix timestamp for the target date and uses it to create a unique CSS selector (`div[data-time='...']`), resulting in a 100% accurate date selection.

3.  **Intercepted Clicks (`ElementClickInterceptedException`):**
    *   **Challenge:** Elements like the calendar's "Accept" button, although present in the DOM, were not "clickable" by Selenium because they were off-screen or obscured by other elements.
    *   **Solution:** Forced clicks were performed using JavaScript execution (`driver.execute_script("arguments[0].click();", element)`). This method is far more robust as it triggers the click event directly on the DOM element, bypassing visibility and scroll-state checks.

---

### 🚀 Deployment & Setup

This script is designed for easy deployment on GitHub Actions.

#### 1. Fork the Repository

Fork this repository to your own GitHub account.

#### 2. Configure Secrets

In your forked repository, go to `Settings` > `Secrets and variables` > `Actions` and add the following "Repository secrets":

*   `SENDER_EMAIL`: Your Gmail address.
*   `SENDER_APP_PASSWORD`: Your 16-digit Google App Password.
*   `RECIPIENT_EMAIL`: The email address that will receive the notifications.

#### 3. Enable the Workflow

The workflow defined in `.github/workflows/main.yml` will automatically trigger on the next scheduled interval (`cron`). You can also run it manually from the "Actions" tab.

---

### 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
