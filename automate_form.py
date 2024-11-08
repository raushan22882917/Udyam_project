# udyam\automate_form.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from datetime import datetime 
from time import sleep
from PIL import Image
from io import BytesIO
import requests
import re
import os
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
)
import webdriver_manager
from webdriver_manager.firefox import GeckoDriverManager
import time

driver = None

def get_driver():
    global driver
    if driver is None:
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument('--ignore-certificate-errors')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


"""
def get_driver():
    global driver
    if driver is None:
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        #  Uncomment the line below if you want to run Chrome in headless mode
        chrome_options.add_argument("--headless")
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service)
        driver = webdriver.Chrome(options=chrome_options)
    return driver
"""

def close_driver():
    global driver
    if driver:
        driver.quit()
    driver = None


def initiate_adhar(adhar, name):
    driver = get_driver()
    try:
        driver.get("https://udyamregistration.gov.in/UdyamRegistration.aspx")

        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located(
                (By.NAME, "ctl00$ContentPlaceHolder1$txtadharno")
            )
        )

        driver.find_element(By.NAME, "ctl00$ContentPlaceHolder1$txtadharno").send_keys(
            adhar
        )
        driver.find_element(
            By.NAME, "ctl00$ContentPlaceHolder1$txtownername"
        ).send_keys(name)

        driver.find_element(
            By.NAME, "ctl00$ContentPlaceHolder1$btnValidateAadhaar"
        ).click()

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.NAME, "ctl00$ContentPlaceHolder1$txtOtp1")
            )
        )

        return "OTP page ready"
    except Exception as e:
        # close_driver()
        return f"Error in initiate_adhar: {str(e)}"


def submit_otp(otp):
    driver = get_driver()
    try:
        driver.find_element(By.NAME, "ctl00$ContentPlaceHolder1$txtOtp1").send_keys(otp)
        driver.find_element(By.NAME, "ctl00$ContentPlaceHolder1$btnValidate").click()

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.ID, "ctl00_ContentPlaceHolder1_ddlTypeofOrg")
            )
        )

        return "OTP submitted successfully"
    except Exception as e:
        # close_driver()
        return f"Error in submit_otp: {str(e)}"


def submit_pan(pan_data):
    driver = get_driver()
    try:
        # Wait for the dropdown to be present
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_ddlTypeofOrg"))
        )

        # Select 'Proprietary' using JavaScript
        script = """
        var select = document.getElementById('ctl00_ContentPlaceHolder1_ddlTypeofOrg');
        for(var i=0; i<select.options.length; i++) {
            if(select.options[i].text.includes('Proprietary')) {
                select.selectedIndex = i;
                select.dispatchEvent(new Event('change'));
                break;
            }
        }
        """
        driver.execute_script(script)

        # Wait for 5 seconds
        time.sleep(5)

        # Wait for the PAN input field to be visible and interactable
        WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_txtPan"))
        )

        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtPan").send_keys(pan_data["pan"])
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtPanName").send_keys(pan_data["pan_name"])
        
        # Convert date format to DD/MM/YYYY
        dob = datetime.strptime(pan_data["dob"], "%Y-%m-%d").strftime("%d/%m/%Y")
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtdob").send_keys(dob)

        # Wait for the preloader to disappear
        WebDriverWait(driver, 30).until(
            EC.invisibility_of_element_located((By.ID, "preloader"))
        )

        # Try to click the checkbox, if it fails, use JavaScript
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_chkDecarationP"))
            ).click()
        except ElementClickInterceptedException:
            driver.execute_script(
                "document.getElementById('ctl00_ContentPlaceHolder1_chkDecarationP').click();"
            )

        # Wait for 5 seconds
        time.sleep(5)

        # Wait for the PAN Validate button to be clickable
        validate_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_btnValidatePan"))
        )

        # Try to click the button, if it fails, use JavaScript
        try:
            validate_button.click()
        except ElementClickInterceptedException:
            driver.execute_script(
                "document.getElementById('ctl00_ContentPlaceHolder1_btnValidatePan').click();"
            )

        # Wait for 10 seconds
        time.sleep(10)

        # Wait for the Get PAN Data button to appear and be clickable
        get_pan_data_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_btnGetPanData"))
        )

        # Try to click the button, if it fails, use JavaScript
        try:
            get_pan_data_button.click()
        except ElementClickInterceptedException:
            driver.execute_script(
                "document.getElementById('ctl00_ContentPlaceHolder1_btnGetPanData').click();"
            )

        # Wait for the GSTIN radio buttons to appear
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_rblWhetherGstn"))
        )
        print("GSTIN radio buttons found")

        # Select the appropriate GSTIN option
        gstin_option = pan_data.get("have_gstin", "Exempted")  # Default to "Exempted" if not provided
        gstin_value = "1" if gstin_option == "Yes" else "3" if gstin_option == "No" else "3"
        gstin_id = f"ctl00_ContentPlaceHolder1_rblWhetherGstn_{int(gstin_value) - 1}"
        print(f"Attempting to select GSTIN option: {gstin_option}, ID: {gstin_id}")

        gstin_radio = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, gstin_id))
        )
        print("GSTIN radio button found and clickable")

        try:
            gstin_radio.click()
            print("GSTIN radio button clicked")
        except Exception as e:
            print(f"Failed to click GSTIN radio button: {str(e)}")
            driver.execute_script(f"document.getElementById('{gstin_id}').click();")
            print("GSTIN radio button clicked using JavaScript")

        # Wait for the mobile input field to appear
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtmobile"))
        )
        print("Mobile input field found")

        return "PAN and GSTIN details submitted successfully"
    except TimeoutException as e:
        print(f"Timeout Exception: {str(e)}")
        return f"Error in submit_pan: Timeout waiting for element. {str(e)}"
    except Exception as e:
        print(f"General Exception: {str(e)}")
        return f"Error in submit_pan: {str(e)}"




def select_option_by_regex(dropdown_element, user_input):
    # Create a Select object for the dropdown
    select = Select(dropdown_element)

    # Normalize the user's input to uppercase for matching
    user_input = user_input.upper()

    # Iterate through the options in the dropdown to find a regex match
    for option in select.options:
        option_text = option.text.upper()

        # Extract the district name from the option text
        district_name = option_text.split('.')[-1].strip()

        # Use regex to match the user's input with the district name
        if re.search(rf"\b{re.escape(user_input)}\b", district_name):
            select.select_by_visible_text(option.text)
            return

    # If no match is found, try a more lenient search
    for option in select.options:
        option_text = option.text.upper()
        if user_input in option_text:
            select.select_by_visible_text(option.text)
            return

    # Raise an error if no match is found
    raise ValueError(f"Could not locate element with matching text for: {user_input}")


def submit_form(form_data):
    driver = get_driver()

    try:
        # Wait for the form to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtmobile"))
        )

        # Fill in form fields
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtmobile").send_keys(form_data["mobile"])
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtemail").send_keys(form_data["email"])

        # Social Category
        social_category_map = {"General": "0", "SC": "1", "ST": "2", "OBC": "3"}
        driver.find_element(
            By.ID,
            f"ctl00_ContentPlaceHolder1_rdbcategory_{social_category_map.get(form_data.get('social_category', 'General'), '0')}",
        ).click()

        # Gender
        gender_map = {"M": "0", "F": "1", "O": "2"}
        driver.find_element(
            By.ID,
            f"ctl00_ContentPlaceHolder1_rbtGender_{gender_map.get(form_data['gender'], '0')}",
        ).click()

        # Specially Abled
        specially_abled_map = {"Y": "0", "N": "1"}
        driver.find_element(
            By.ID,
            f"ctl00_ContentPlaceHolder1_rbtPh_{specially_abled_map.get(form_data.get('specially_abled', 'N'), '1')}",
        ).click()

        # Fill in the form fields
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtenterprisename").send_keys(form_data.get("enterprise_name", form_data["pan_name"]))
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtUnitName").send_keys(form_data.get("unit_name", form_data["pan_name"]))

        # Click the "Add Unit" button
        add_unit_button = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_btnAddUnit")
        add_unit_button.click()

        # Wait for 2 seconds
        sleep(2)

        # Create a Select object and choose the first option
        dropdown_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_ddlUnitName"))
        )
        select = Select(dropdown_element)
        select.select_by_index(1)

        # Fill address details
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtPFlat"))
        ).send_keys(form_data["premises_number"])

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtPBuilding"))
        ).send_keys(form_data["building_name"])

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtPVillageTown"))
        ).send_keys(form_data["village_town"])

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtPBlock"))
        ).send_keys(form_data["block"])

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtPRoadStreetLane"))
        ).send_keys(form_data["road_street_lane"])

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtPCity"))
        ).send_keys(form_data["city"])

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtPpin"))
        ).send_keys(form_data["pincode"])

        # Select state
        state_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_ddlPState"))
        )
        select_option_by_regex(state_dropdown, form_data["state"])

        # Wait for the district dropdown to load options
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_ddlPDistrict option:not([value='0'])"))
        )

        # Select district
        district_dropdown = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_ddlPDistrict")
        select_option_by_regex(district_dropdown, form_data["district"])

        # Click the "Add Plant" button
        add_plant_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_BtnPAdd"))
        )
        add_plant_button.click()

        # Wait for 4 seconds
        time.sleep(4)

        # Official address of the enterprise (same as plant address)
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtOffFlatNo").send_keys(form_data["premises_number"])
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtOffBuilding").send_keys(form_data["building_name"])
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtOffVillageTown").send_keys(form_data["village_town"])
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtOffBlock").send_keys(form_data["block"])
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtOffRoadStreetLane").send_keys(form_data["road_street_lane"])
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtOffCity").send_keys(form_data["city"])
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtOffPin").send_keys(form_data["pincode"])

        # Select state (same as plant address)
        state_dropdown = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_ddlstate")
        select_option_by_regex(state_dropdown, form_data["state"])

        # Wait for the district dropdown to load options
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_ddlDistrict option:not([value='0'])"))
        )

        # Select district (same as plant address)
        district_dropdown = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_ddlDistrict")
        select_option_by_regex(district_dropdown, form_data["district"])

        # Click the "Get Latitude & Longitude" button
        get_lat_long_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_Button1"))
        )
        get_lat_long_button.click()

        # Store the current window handle (parent window)
        parent_window = driver.current_window_handle

        # Wait for the new window to open and switch to it
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        all_windows = driver.window_handles
        new_window = [window for window in all_windows if window != parent_window][0]
        driver.switch_to.window(new_window)

        # Wait for the map to load
        wait = WebDriverWait(driver, 40)

        # Wait for the map div to be present
        map_div = wait.until(EC.presence_of_element_located((By.ID, 'mapDiv')))
        print("Map div found")

        # Wait for SVG to load
        svg = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'svg')))
        print("SVG element found")

        # Implement a retry mechanism for finding path elements
        max_retries = 5
        for attempt in range(max_retries):
            paths = driver.find_elements(By.CSS_SELECTOR, 'path')
            if paths:
                print(f"Found {len(paths)} path elements")
                district_path = paths[0]
                actions = ActionChains(driver)
                
                # Scroll the element into view
                driver.execute_script("arguments[0].scrollIntoView();", district_path)
                
                # Click the path
                actions.move_to_element(district_path).click().perform()
                print("Clicked on a path element")
                time.sleep(2)  # Wait for 2 seconds after clicking
                break
            else:
                print(f"No path elements found. Attempt {attempt + 1} of {max_retries}")
                time.sleep(2)  # Wait for 2 seconds before retrying
        else:
            print("Failed to find path elements after all attempts")

        # Wait for latitude and longitude fields to be visible
        latitude = wait.until(EC.visibility_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_txtlatitude1')))
        longitude = wait.until(EC.visibility_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_txtlongitude1')))

        latitude_value = latitude.get_attribute('value')
        longitude_value = longitude.get_attribute('value')

        print(f'Latitude: {latitude_value}')
        print(f'Longitude: {longitude_value}')

        # Click the OK button
        ok_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.btn.btn-primary[onclick="f2();"]')))
        ok_button.click()
        print("Clicked the OK button")
        time.sleep(2)

        # Switch back to the original window
        driver.switch_to.window(parent_window)

        # Date of incorporation (convert to DD/MM/YYYY format)
        incorporation_date = datetime.strptime(form_data["date_of_incorporation"], "%Y-%m-%d").strftime("%d/%m/%Y")
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtdateIncorporation").send_keys(incorporation_date)

        # Date of Commencement (use incorporation date if not provided)
        commencement_date = form_data.get("date_of_commencement", form_data["date_of_incorporation"])
        commencement_date = datetime.strptime(commencement_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtcommencedate").send_keys(commencement_date)

        # Bank Details
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtBankName").send_keys(form_data["bank_name"])
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtaccountno").send_keys(form_data["account_number"])
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtifsccode").send_keys(form_data["ifsc_code"])

        # Previous Udyog Aadhaar Number (UAN)
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_rdbPrevUAN_1").click()  # Select "No" for previous UAN

        return "Form submitted successfully"
    except Exception as e:
        return f"Error submitting form: {str(e)}"


def automate_form_next(major_activity, second_form_section, nic_codes, employee_counts, investment_data, turnover_data, district):
    driver = get_driver()  # Get the WebDriver instance
    if not driver:
        return {"status": "error", "message": "Failed to initialize WebDriver"}

    def safe_find_element(by, value, timeout=15):
        try:
            return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            logging.warning(f"Element not found: {value}")
            return None

    def safe_click(element):
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(element))
            element.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", element)
        except Exception as e:
            logging.error(f"Error clicking element: {e}")

    def select_option_by_text(select_element, text):
        try:
            select = Select(select_element)
            select.select_by_visible_text(text)
            return True
        except Exception as e:
            logging.error(f"Error selecting option {text}: {e}")
            return False

    try:
        # Major Activity of Unit
        activity_map = {"Mfg": "1", "Service": "2", "Trading": "2"}
        major_activity_id = f'ctl00_ContentPlaceHolder1_rdbCatgg_{activity_map.get(major_activity, "1")}'
        radio_button_script = f"document.getElementById('{major_activity_id}').click();"

        # Major Activity Under Services (if applicable)
        if major_activity == "2":  # Services
            second_form_section_id = f'ctl00_ContentPlaceHolder1_rdbSubCategg_{int(second_form_section) - 1}'
            safe_click(safe_find_element(By.ID, second_form_section_id))
            logging.info(f"Selected second form section: {second_form_section}")

        # NIC Code Selection
        category_radios = {
            "Manufacturing": "//table[@id='ctl00_ContentPlaceHolder1_rdbCatggMultiple']//label[contains(text(),'Manufacturing')]",
            "Services": "//table[@id='ctl00_ContentPlaceHolder1_rdbCatggMultiple']//label[contains(text(),'Services')]",
            "Trading": "//table[@id='ctl00_ContentPlaceHolder1_rdbCatggMultiple']//label[contains(text(),'Trading')]"
        }

        category_element = safe_find_element(By.XPATH, category_radios[nic_codes[0]['category']])
        if category_element:
            safe_click(category_element)
            logging.info(f"Selected category: {nic_codes[0]['category']}")
        else:
            logging.warning(f"Category element not found for: {nic_codes[0]['category']}")

        time.sleep(3)  # Wait for the page to load

        for nic_code in nic_codes:
            two_digit = safe_find_element(By.XPATH, "//select[@name='ctl00$ContentPlaceHolder1$ddl2NicCode']")
            if two_digit and select_option_by_text(two_digit, nic_code['2_digit']):
                logging.info(f"Selected 2-digit NIC code: {nic_code['2_digit']}")

            four_digit = safe_find_element(By.XPATH, "//select[@name='ctl00$ContentPlaceHolder1$ddl4NicCode']")
            if four_digit and select_option_by_text(four_digit, nic_code['4_digit']):
                logging.info(f"Selected 4-digit NIC code: {nic_code['4_digit']}")

            five_digit = safe_find_element(By.XPATH, "//select[@name='ctl00$ContentPlaceHolder1$ddl5NicCode']")
            if five_digit and select_option_by_text(five_digit, nic_code['5_digit']):
                logging.info(f"Selected 5-digit NIC code: {nic_code['5_digit']}")

            add_activity = safe_find_element(By.XPATH, "//input[@name='ctl00$ContentPlaceHolder1$btnAddMore'][@value='Add Activity']")
            if add_activity:
                safe_click(add_activity)
                logging.info("Added activity")
            else:
                logging.warning("Add Activity button not found")

            time.sleep(5)  # Wait for the page to load

        # Number of persons employed
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtNoofpersonMale").send_keys(str(employee_counts.get("male", 0)))
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtNoofpersonFemale").send_keys(str(employee_counts.get("female", 0)))
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtNoofpersonOthers").send_keys(str(employee_counts.get("others", 0)))

        # Investment in Plant and Machinery or Equipment
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtDepCost").send_keys(str(investment_data.get("wdv", 500000)))
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtExCost").send_keys(str(investment_data.get("exclusion_cost", 200000)))

        # Turnover
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtTotalTurnoverA").send_keys(str(turnover_data.get("total_turnover", 0)))
        driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtExportTurnover").send_keys(str(turnover_data.get("export_turnover", 0)))

        # Additional registrations (all set to "No")
        no_buttons = [
            '#ctl00_ContentPlaceHolder1_rblGeM_1',
            '#ctl00_ContentPlaceHolder1_rblTReDS_1',
            '#ctl00_ContentPlaceHolder1_rblNCS_1',
            '#ctl00_ContentPlaceHolder1_rblnsic_1',
            '#ctl00_ContentPlaceHolder1_rblnixi_1',
            '#ctl00_ContentPlaceHolder1_rblsid_1'
        ]

        for button_id in no_buttons:
            try:
                no_button = driver.find_element(By.CSS_SELECTOR, button_id)
                driver.execute_script("arguments[0].click();", no_button)
                logging.info(f"Clicked 'No' button: {button_id}")
            except Exception as e:
                logging.error(f'Error selecting "No" button with ID {button_id}: {str(e)}')

        # District Industries Centre
        district_dropdown = safe_find_element(By.ID, "ctl00_ContentPlaceHolder1_ddlDIC")
        if district_dropdown:
            if select_option_by_text(district_dropdown, district):
                logging.info(f"Selected district: {district}")
            else:
                logging.warning(f"Failed to select district: {district}")
        else:
            logging.warning("District dropdown not found")

        # Final submission
        submit_button = safe_find_element(By.ID, "ctl00_ContentPlaceHolder1_btnsubmit")
        if submit_button:
            safe_click(submit_button)
            logging.info("Clicked initial submit button")
        else:
            logging.error("Initial submit button not found")
            return {"status": "error", "message": "Initial submit button not found"}

        # Wait for 5 seconds
        time.sleep(5)

        # Wait for the CAPTCHA image to load
        captcha_element = safe_find_element(By.ID, "ctl00_ContentPlaceHolder1_ImgCaptcha", timeout=30)
        if not captcha_element:
            logging.error("CAPTCHA image not found after submission")
            return {"status": "error", "message": "CAPTCHA image not found"}

        # Get the CAPTCHA image URL
        captcha_url = captcha_element.get_attribute("src")

        # Return the CAPTCHA URL to the caller
        return {"status": "success", "message": "CAPTCHA required", "captcha_url": captcha_url}

    except Exception as e:
        logging.error(f"Unexpected error in form submission: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        close_driver()

    return result


def safe_find_element(by, value, timeout=15):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except TimeoutException:
        logging.warning(f"Element not found: {value}")
        return None

def safe_click(element):
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(element))
        element.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", element)
    except Exception as e:
        logging.error(f"Error clicking element: {e}")

def submit_captcha_and_complete(registration_id, captcha_code):
    driver = get_driver()
    try:
        # Enter the CAPTCHA code
        captcha_input = safe_find_element(By.ID, "ctl00_ContentPlaceHolder1_txtCaptcha")
        if captcha_input:
            captcha_input.clear()
            captcha_input.send_keys(captcha_code)
            logging.info("Entered CAPTCHA code")
        else:
            logging.error("CAPTCHA input field not found")
            return {"status": "error", "message": "CAPTCHA input field not found"}

        # Click the final submit button
        final_submit_button = safe_find_element(By.ID, "ctl00_ContentPlaceHolder1_btnSubmit")
        if final_submit_button:
            safe_click(final_submit_button)
            logging.info("Clicked final submit button")
        else:
            logging.error("Final submit button not found")
            return {"status": "error", "message": "Final submit button not found"}

        # Wait for the submission to complete
        success_message_element = safe_find_element(By.ID, "ctl00_ContentPlaceHolder1_lblMsg", timeout=30)
        if success_message_element:
            success_message = success_message_element.text
            if "successfully" in success_message.lower():
                logging.info("Form submitted successfully!")
                return {"status": "success", "message": success_message}
            else:
                logging.warning(f"Form submission may have failed. Message: {success_message}")
                return {"status": "warning", "message": success_message}
        else:
            logging.error("Success message element not found")
            return {"status": "error", "message": "Success message element not found"}

    except Exception as e:
        logging.error(f"Unexpected error in CAPTCHA submission: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        close_driver()

    return result

def get_captcha_url(registration_id):
    driver = get_driver()
    try:
        captcha_element = safe_find_element(By.ID, "ctl00_ContentPlaceHolder1_ImgCaptcha", timeout=30)
        if not captcha_element:
            logging.error("CAPTCHA image not found")
            return None

        captcha_url = captcha_element.get_attribute("src")
        return captcha_url
    except Exception as e:
        logging.error(f"Error getting CAPTCHA URL: {str(e)}")
        return None


