from playwright.sync_api import sync_playwright
import csv
import re
import time

def scrape_penske(city_state, pickup_day, save_to_csv=False):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Set to False if you want to SEE it
        page = browser.new_page()

        page.goto("https://www.pensketruckrental.com/")

        # 1. Return Location = Same Location
        page.wait_for_selector('fieldset.quote_return_location .quote-select', state='visible')
        page.click('fieldset.quote_return_location .quote-select')
        page.wait_for_selector('span.quote-option[data-value="same-location"]', state='visible')
        page.click('span.quote-option[data-value="same-location"]')

        # 2. Pickup Location
        page.wait_for_selector('input#pickup_location_txtboxHM', state='visible')
        page.click('input#pickup_location_txtboxHM')
        page.fill('input#pickup_location_txtboxHM', city_state)
        page.wait_for_timeout(1500)  # Wait for dropdown suggestions
        page.keyboard.press('ArrowDown')
        page.keyboard.press('Enter')


        # 3. Pickup Date
        page.click('input#mat-input-1')
        page.wait_for_timeout(1500)  # Wait for calendar to load

        # 4. Select pickup date twice (same day rental)
        page.locator(f'span:text("{pickup_day}")').first.click()
        page.locator(f'span:text("{pickup_day}")').nth(1).click()

        # 5. Click Continue button inside calendar
        page.click('button:has-text("Continue")')

        # 6. Click Search
        page.click('button#submitbuttonHM')

        # 7. Wait for truck cards to load
        page.wait_for_selector('div.rdt-truck-list__truck-grid')
        time.sleep(2)  # Let results fully render

        # 8. Scrape all truck results
        trucks = page.locator('div.rdt-truck-list__truck-grid')

        truck_data = []

        for i in range(trucks.count()):
            truck = trucks.nth(i)

            # Truck Title
            title = truck.locator('p.rdt-truck-list__truck-title').text_content()
            title = title.strip() if title else ""

            # Big price (dollars)
            price_dollars = truck.locator('span.rdt-truck-list__big-price').text_content()
            price_dollars = price_dollars.strip().replace('$', '') if price_dollars else "0"

            # Small price (cents)
            price_cents = truck.locator('span.rdt-truck-list__small-price').text_content()
            if price_cents:
                price_cents = price_cents.strip()
                price_cents = price_cents.replace('/day', '').replace('.', '')
            else:
                price_cents = "00"

            # Full Day Rate
            day_rate = f"{price_dollars}.{price_cents}"

            # Mileage Rate
            mileage_rate_text = truck.locator('div.rdt-truck-list__rateperUnit').text_content()
            mileage_rate = ""
            if mileage_rate_text:
                match = re.search(r'\$([\d\.]+)', mileage_rate_text)
                if match:
                    mileage_rate = match.group(1)

            truck_data.append({
                "Truck Type": title,
                "Daily Rate ($)": day_rate,
                "Mileage Rate ($/mile)": mileage_rate,
            })

        # 9. Print results
        print("\n--- Scraped Truck Data ---")
        for truck in truck_data:
            print(truck)

        # 10. Optional: Save to CSV
        if save_to_csv:
            keys = truck_data[0].keys()
            with open('penske_truck_rates.csv', 'w', newline='') as output_file:
                dict_writer = csv.DictWriter(output_file, keys)
                dict_writer.writeheader()
                dict_writer.writerows(truck_data)
            print("\nSaved to 'penske_truck_rates.csv'")

        browser.close()

# ----------------------------------------------
# 🔥 Test Call (Phoenix, AZ, Pickup April 30)
# ----------------------------------------------
if __name__ == "__main__":
    scrape_penske(
        city_state="Phoenix, AZ",
        pickup_day="30",
        save_to_csv=True  # Set False if you only want print
    )
