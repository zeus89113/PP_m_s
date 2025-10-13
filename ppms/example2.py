from selenium import webdriver
import time

# Create a new instance of the Chrome driver
# This will open a new Chrome browser window
driver = webdriver.Chrome()

# Navigate to the specified URL
driver.get("https://www.google.com")

# Print the title of the page to the console
print(f"The title of the page is: {driver.title}")

# Wait for 5 seconds to see the result
time.sleep(5)

# Close the browser window
driver.quit()