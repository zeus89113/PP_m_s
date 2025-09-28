import unittest
import time
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from power_plant_app import create_app, db
from power_plant_app.models import User
from werkzeug.security import generate_password_hash

class SeleniumAuthTests(unittest.TestCase):
    def setUp(self):
        """Called before each test."""
        # 1. Set up the app to use a temporary, in-memory database for testing
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
        })
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # 2. Create all the database tables
        db.create_all()
        
        # 3. CREATE AND SAVE THE TEST USERS TO THE DATABASE
        admin_user = User(username='zeus', password_hash=generate_password_hash('zeus'), role='admin')
        operator_user = User(username='harris', password_hash=generate_password_hash('harris'), role='operator')
        db.session.add(admin_user)
        db.session.add(operator_user)
        db.session.commit()
        
        # 4. Start the Flask server in a background thread
        self.server_thread = Thread(target=self.app.run, kwargs={'use_reloader': False})
        self.server_thread.daemon = True
        self.server_thread.start()
        time.sleep(1)

        # 5. Set up the Selenium WebDriver
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        self.driver.implicitly_wait(5)

    def tearDown(self):
        """Called after each test."""
        self.driver.quit()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _login(self, username, password):
        self.driver.get("http://127.0.0.1:5000/auth/login")
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5) 


    def test_successful_login_and_logout(self):
        """Test 1: Can a user log in and then log out successfully?"""
        print("\nRunning test: Successful Login and Logout")
        self._login('zeus', 'zeus')
        self.assertIn("Plant Overview", self.driver.title)
        

        logout_link = self.driver.find_element(By.CSS_SELECTOR, "a[href='/auth/logout']")
        logout_link.click()
        time.sleep(0.5)
        self.assertIn("Log In", self.driver.title)

    def test_failed_login_shows_error(self):
        """Test 2: Does an invalid login attempt show a flash message?"""
        print("Running test: Failed Login Shows Error")
        self._login('zeus', 'harris')
        
        self.assertIn("Log In", self.driver.title)
        
        error_message = self.driver.find_element(By.CLASS_NAME, "flash-error").text
        self.assertIn("Invalid username or password", error_message)

    def test_reactor_module_is_present_after_login(self):
        """Test 3: After logging in, is the 'Reactor 1' module visible?"""
        print("Running test: Reactor Module is Present After Login")
        self._login('harris', 'harris')
        

        reactor_block = self.driver.find_element(By.ID, "reactor_1")
        self.assertIsNotNone(reactor_block)
        
        module_name = reactor_block.find_element(By.CLASS_NAME, "module-name").text
        self.assertEqual("Reactor 1", module_name)

    def test_admin_can_access_reports(self):
        """Test 5: Can an admin successfully access the reports page?"""
        print("Running test: Admin Can Access Reports")
        self._login('zeus', 'zeus')
        
        # Navigate using the link
        self.driver.find_element(By.LINK_TEXT, "Reports").click()
        time.sleep(0.5)
        
        # Check if we are on the correct page
        self.assertIn("Module Reports", self.driver.title)
        heading = self.driver.find_element(By.TAG_NAME, "h1").text
        self.assertEqual("Historical Module Reports", heading)


if __name__ == '__main__':
    unittest.main(verbosity=2)