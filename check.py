import time
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BOT_TOKEN = "8158756480:AAHqxuED7sTs0SOf1bmfHW8vvlbkhBLauG0"
CHAT_ID = "85428299"

options = uc.ChromeOptions()
options.headless = True  # Set True for GitHub Actions; False for debugging locally
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-blink-features=AutomationControlled')

driver = uc.Chrome(use_subprocess=True, options=options)
wait = WebDriverWait(driver, 20)

def check_termin():
    termins_available = False
    try:
        url = "https://termine.staedteregion-aachen.de/auslaenderamt/select2?md=1"
        driver.get(url)

        # Handle cookie pop-up
        try:
            accept_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="cookie_msg_btn_yes"]')))
            accept_btn.click()
        except:
            print("No cookie banner or already accepted")

        # Expand RWTH section
        rwth_section = wait.until(EC.element_to_be_clickable((
            By.XPATH, '//*[@id="header_concerns_accordion-455"]'
            #By.XPATH, '//*[@id="header_concerns_accordion-461"]' #TODO ONLY FOR DEBUGGING
        )))
        rwth_section.click()

        # Click "+" next to RWTH Studenten
        student_row_plus = wait.until(EC.element_to_be_clickable((
            By.XPATH, '//*[@id="button-plus-286"]/span'
            #By.XPATH, '//*[@id="button-plus-310"]/span' #TODO ONLY FOR DEBUGGING
        )))
        student_row_plus.click()
        print("✅ Clicked '+' for RWTH Studenten")

        # Click first WeiterButton
        next_button = wait.until(EC.element_to_be_clickable((By.ID, 'WeiterButton')))
        next_button.click()
        print("➡️ Proceeded to confirmation modal")

        # Click OK in modal
        ok_button = wait.until(EC.element_to_be_clickable((By.ID, "OKButton")))
        ok_button.click()
        print("✅ Clicked OK in modal")
        time.sleep(0.05)
        # Click second WeiterButton
        next_button = wait.until(EC.element_to_be_clickable((By.ID, 'WeiterButton')))
        next_button.click()
        print("Proceeded to availability check")
        # Check for availability
        try:
            driver.find_element(
                By.XPATH, '//h2[contains(@class, "h1like") and contains(text(), "Kein freier Termin verfügbar")]'
            )
            print("❌ No appointments available.")
        except:
            print("Appointment mat be available!")
            termins_available = True
            book_any_termin()

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
    finally:
        if(termins_available):
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
            screenshot_path = f"final_screenshot_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot saved as {screenshot_path}")
                    # Send the screenshot to Telegram for manual verification
            url_photo = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(screenshot_path, 'rb') as photo:
                requests.post(url_photo, data={
                    "chat_id": CHAT_ID,
                    "caption": "📋 Final page after booking attempt:"
                }, files={"photo": photo})

        driver.quit()
        print("🧹 Driver closed.")

def find_slots(panel_id :str):
    try:
      # Locate the matrix of slots within the panel
      slot_matrix = wait.until(EC.presence_of_element_located((
        By.XPATH, f'//*[@id="{panel_id}"]/table/tbody'
      )))
      for i in range(1, 6):
        for j in range(2, 4):
          try:
              # Find the first clickable button in the slot matrix
              slot_button = wait.until(EC.presence_of_element_located((
                 By.CSS_SELECTOR, f'#{panel_id} tr:nth-child({i}) > td:nth-child({j}) .suggest_btn')
                
              ))
              driver.execute_script("arguments[0].scrollIntoView(true);", slot_button)
              if slot_button.get_attribute("disabled") is None:
                  print(f"✅ Clickable Slot found")
                  slot_button.click()
                  return
              
          except Exception as e:
              print(f"Error in Time slot selection phase: {e}")
    except Exception as e:
      print(f"Error while finding slots in panel {panel_id}: {e}")

def wait_for_captcha_solution(captcha_image, termin_title):
  # Get current latest update ID to ignore earlier messages
  url_updates = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
  last_update_id = None
  response = requests.get(url_updates)
  data = response.json()
  updates = data.get('result', [])
  if updates:
      last_update_id = updates[-1]['update_id']
  
  url1 = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
  with open(captcha_image, 'rb') as photo:
    requests.post(url1, data={"chat_id": CHAT_ID, "caption": f"Termin for {termin_title}🧩 CAPTCHA for, please solve and reply here:"}, files={"photo": photo})
  print("📨 Waiting for your CAPTCHA response in Telegram...")
  while True:
    response = requests.get(url_updates)
    data = response.json()
    updates = data.get('result', [])
    new_updates = [u for u in updates if u['update_id'] > (last_update_id or 0)]

    if new_updates:
        message = new_updates[-1]['message']
        last_update_id = new_updates[-1]['update_id']
        if 'text' in message:
            solution = message['text']
            print(f"🧠 Got CAPTCHA solution: {solution}")
            return solution

    time.sleep(1)  # Wait 1s before polling again 


   
def book_any_termin():
    for i in range(1, 16):  # Assuming the IDs range from ui-id-1 to ui-id-15
      try:
        collapsable_item = wait.until(EC.element_to_be_clickable((
          By.XPATH, f'//*[@id="ui-id-{i}"]'
        )))
        # Check the title of the collapsable item e.g. title="Mittwoch, 23.04.2025"
        title = collapsable_item.get_attribute('title')
        date_part = title.split(",")[1].strip()  # e.g., "23.04.2025"
        month = int(date_part.split(".")[1])  # Extract the month (e.g., 4 for April)
        if month != 5:  # Skip if the month is not May
            print(f"❌ Skipping date {date_part} as it is not in May.")
            continue
        else:
          driver.execute_script("arguments[0].scrollIntoView(true);", collapsable_item)
          collapsable_item.click()
          print(f"✅ Clicked collapsable item")
          break
      except Exception as e:
        print(f"❌ Could not click collapsable item with ID ui-id-{i}: {e}")
      
    panel_id = collapsable_item.get_attribute('aria-controls')
    print(f"Panel ID: {panel_id}")
    # If a collapsable item is found and clicked, break the loop and start the function
    try:
      find_slots(panel_id)
      ja_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#TevisDialog > div > div > div.modal-footer > button.sel_button.btn.btn-primary.pull-right.fifty.btn-ok')))
      driver.execute_script("arguments[0].scrollIntoView(true);", ja_button)
      time.sleep(0.5)
      ja_button.click()
      first_name_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="vorname"]')))
      first_name_input.send_keys("Pouya")
      last_name_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="nachname"]')))
      last_name_input.send_keys("Shekarchizadeh Esfahani")
      email_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="email"]')))
      email_input.send_keys("pooya.shekarchi@icloud.com")
      email_repeat_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="emailwhlg"]')))
      email_repeat_input.send_keys("pooya.shekarchi@icloud.com")
      tel_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="tel"]')))
      tel_input.send_keys("017685627145")
      year_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="geburtsdatumYear"]')))
      year_input.send_keys("1998")
      month_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="geburtsdatumMonth"]')))
      month_input.send_keys("11")
      day_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="geburtsdatumDay"]')))
      day_input.send_keys("02")
      comment_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="comment"]')))
      comment_input.send_keys("Ich möchte einen früheren Termin, ich werde natürlich meinen vorherigen Termin stornieren, sobald Sie die neue Terminbuchung bitte bestätigen.")
      checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="cal-reservation"]/div/div[8]/label/span[1]')))
      checkbox.click()
      captcha_img_element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="captcha_image"]')))
      captcha_img_element.screenshot("captcha.png")
      captcha_solution = wait_for_captcha_solution("captcha.png",title)
      captcha_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="captcha_result"]')))
      captcha_input.send_keys(captcha_solution)
      submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="chooseTerminButton"]')))
      submit_button.click() 

    except Exception as e:
      print(f"Error while booking appointment: {e}")
  
if __name__ == "__main__":
    print("🔍 Checking for appointments...")
    check_termin()
    print("✅ Check completed.")
    print("🔚 Script finished.")
