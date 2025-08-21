# -*- coding: utf-8 -*-
"""
Web scraping script to monitor train tickets on Renfe.com.

Version 11.0 - Final International Version. This version includes a fully
rewritten results page parsing logic to match the actual HTML structure,
ensuring accurate availability detection.

Author: Alberto Ines
Date: 21/08/2025
"""

import os
import smtplib
import ssl
import time
from datetime import datetime

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- SELENIUM LIBRARIES ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- AUTOMATIC DRIVER MANAGER ---
from webdriver_manager.chrome import ChromeDriverManager

# ==============================================================================
# --- USER CONFIGURATION ---
# ==============================================================================

# -- Trip Details --
ORIGIN_CITY = "Barcelona"
DESTINATION_CITY = "Madrid"
# Format: "DD/MM/YYYY"
DEPARTURE_DATE = "24/10/2025"
# Format: "HH:MM"
TARGET_DEPARTURE_TIME = "07:27"

# -- Email Notification Details --
# Securely read from GitHub Secrets or environment variables
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_APP_PASSWORD = os.environ.get("SENDER_APP_PASSWORD")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

# -- Script Settings --
# The scheduled execution is handled by GitHub Actions, so no interval is needed here.
HEADLESS_MODE = True  # Must be True for server execution

# ==============================================================================
# --- END OF CONFIGURATION ---
# ==============================================================================

def setup_driver():
    """Configures and initializes the Selenium WebDriver."""
    print("Setting up Chrome driver...")
    options = webdriver.ChromeOptions()
    if HEADLESS_MODE:
        options.add_argument("--headless")
    
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def send_notification_email():
    """Builds and sends the notification email."""
    print("Train available! Preparing email notification...")
    message = MIMEMultipart("alternative")
    message["Subject"] = f"✅ Seats Available on your Renfe Train!"
    message["From"] = SENDER_EMAIL
    message["To"] = RECIPIENT_EMAIL
    
    html = f"""
    <html><body>
        <h2>Renfe Ticket Availability Alert!</h2>
        <p>Seats have been found for the train you were monitoring.</p>
        <h3>Trip Details:</h3>
        <ul>
            <li><b>Origin:</b> {ORIGIN_CITY}</li>
            <li><b>Destination:</b> {DESTINATION_CITY}</li>
            <li><b>Date:</b> {DEPARTURE_DATE}</li>
            <li><b>Departure Time:</b> {TARGET_DEPARTURE_TIME}</li>
        </ul>
        <p>Hurry and book your ticket! <a href="https://www.renfe.com" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Renfe.com</a></p>
    </body></html>
    """
    message.attach(MIMEText(html, "html"))
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, message.as_string())
        print(f"Notification email sent successfully to {RECIPIENT_EMAIL}.")
    except Exception as e:
        print(f"Critical error while sending email: {e}")


def fill_autocomplete_field(wait, input_id, list_css_selector, text_to_search):
    """Robustly fills an autocomplete field (Origin/Destination)."""
    print(f"Filling field '{input_id}' with '{text_to_search}'...")
    input_field = wait.until(EC.element_to_be_clickable((By.ID, input_id)))
    input_field.click()
    input_field.clear()
    input_field.send_keys(text_to_search)
    time.sleep(1) 
    suggestion = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, list_css_selector)))
    suggestion.click()
    print(f"Field '{input_id}' successfully selected with '{text_to_search}'.")


def search_and_select_train(driver):
    """Performs the complete search on the Renfe website."""
    wait = WebDriverWait(driver, 30) # Increased wait time for robustness on server
    print("Opening Renfe.com...")
    driver.set_page_load_timeout(60)
    driver.get("https://www.renfe.com/es/es")
    
    try:
        wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))).click()
        print("Cookie policy accepted.")
    except TimeoutException:
        print("Cookie banner not found or already accepted.")
    
    fill_autocomplete_field(wait, "origin", "#awesomplete_list_1 > li", ORIGIN_CITY)
    fill_autocomplete_field(wait, "destination", "#awesomplete_list_2 > li", DESTINATION_CITY)
    
    print("Starting date selection...")
    wait.until(EC.element_to_be_clickable((By.ID, "first-input"))).click()
    
    one_way_label_selector = "//label[contains(normalize-space(), 'Viaje solo ida')]"
    wait.until(EC.element_to_be_clickable((By.XPATH, one_way_label_selector))).click()
    time.sleep(1)
    
    print(f"Searching for date {DEPARTURE_DATE} using its timestamp...")
    target_date_obj = datetime.strptime(DEPARTURE_DATE, "%d/%m/%Y").replace(hour=0, minute=0, second=0, microsecond=0)
    target_timestamp_ms = int(target_date_obj.timestamp() * 1000)
    day_selector = f"div.lightpick__day[data-time='{str(target_timestamp_ms)}']"
    
    date_selected = False
    for _ in range(24): # Loop for up to 24 months
        try:
            day_element = driver.find_element(By.CSS_SELECTOR, day_selector)
            if day_element.is_displayed():
                print("Date found. Selecting day...")
                day_element.click()
                date_selected = True
                break
        except NoSuchElementException:
            next_button_selector = "div.lightpick__nav-action-next"
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, next_button_selector))).click()
            time.sleep(0.5)
            
    if not date_selected:
        raise Exception(f"Could not find the date {DEPARTURE_DATE} in the calendar.")
        
    print("Confirming with 'Aceptar' button (JS mode)...")
    accept_button_selector = "button.lightpick__apply-action-sub"
    accept_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, accept_button_selector)))
    driver.execute_script("arguments[0].click();", accept_button)
    print("Date confirmed.")
    
    print("Clicking 'Buscar billete' button...")
    search_button_selector = "//button[contains(., 'Buscar billete')]"
    wait.until(EC.element_to_be_clickable((By.XPATH, search_button_selector))).click()
    print("Search initiated. Waiting for results...")


def check_availability(driver):
    """
    Parses the results page using the actual HTML structure to identify
    departure time and availability (presence of a price).
    """
    wait = WebDriverWait(driver, 40)
    print("Waiting for the train list to load...")
    try:
        wait.until(EC.visibility_of_element_located((By.ID, "listaTrenesTBodyIda")))
        print("Train list loaded.")
    except TimeoutException:
        if "No hay trenes para la fecha seleccionada" in driver.page_source:
             print("Official Renfe message: No trains available for the selected date.")
             return "no_trains"
        print("Error: Results page did not load in time.")
        raise

    trains = driver.find_elements(By.CSS_SELECTOR, "div.selectedTren")
    print(f"Found {len(trains)} trains. Analyzing...")

    train_found = False
    for train in trains:
        try:
            departure_time_element = train.find_element(By.CSS_SELECTOR, "div.trenes > h5")
            departure_time_text = departure_time_element.text.strip().replace(' h', '')
            
            if departure_time_text == TARGET_DEPARTURE_TIME:
                train_found = True
                print(f"Train departing at {TARGET_DEPARTURE_TIME} found.")
                
                try:
                    train.find_element(By.CSS_SELECTOR, "span.precio-final")
                    print("Price found! Train is AVAILABLE.")
                    return True
                except NoSuchElementException:
                    print("No price found. Train is NOT available (Full or no fares).")
                    return False

        except NoSuchElementException:
            continue
    
    if not train_found:
        print(f"WARNING: Train with departure time {TARGET_DEPARTURE_TIME} not found in the results list.")
    
    return False


def main():
    """
    Main function that performs a SINGLE availability check.
    Designed to be called by an external scheduler like GitHub Actions.
    """
    print("\n" + "="*50)
    print(f"STARTING CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    driver = None
    try:
        driver = setup_driver()
        search_and_select_train(driver)
        is_available = check_availability(driver)

        if is_available is True:
            send_notification_email()
            print("\nSUCCESS! SCRIPT FINISHED.")
        elif is_available == "no_trains":
            print("No scheduled trains found. Finalizing check.")
        else:
            print("Target train is not available. Finalizing check.")

    except Exception as e:
        print(f"\n--- UNEXPECTED ERROR DURING EXECUTION ---")
        print(f"Error: {e.__class__.__name__} - {str(e).splitlines()[0]}")
        if driver:
            screenshot_path = "error_renfe.png"
            try:
                driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved to: {screenshot_path}")
            except Exception as e_ss:
                print(f"Could not save screenshot: {e_ss}")
        raise e 
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
