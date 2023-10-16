import time
import datetime
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException


preferred_rooms = ["218", "219A", "219B", "219C", "226B", "226C", "226D", "314", "315A", "315B", "315C", "320A", "320B", "320C", "320D", "320F", "320H"]
retry_count = 5
max_bookable_slots_per_day = 16
max_bookings = 3


# This function returns the dates based on the text given
# Ex: current-week, next-week, current-month, next-month
def get_dates(text: str):
    dates = []
    current_time = datetime.datetime.now()

    if text.lower() == "current-week":
        pass
    elif text.lower() == "custom":
        dates = [18, 19, 20, 21, 22]
    else:
        dates.append(current_time.day)

    return dates


# Open the date picker & select the particular date selected
def select_the_date(driver: webdriver.Chrome, date: int):
    try:
        go_to_date_button = driver.find_element(By.CLASS_NAME, "fc-goToDate-button")
        go_to_date_button.click()

        date_element = go_to_date_button.find_element(By.XPATH, "//td[text()=" + str(date) + "]")
        date_element.click()

        return True
    except NoSuchElementException as ex:
        print("Element not found", str(ex).split("}")[0])
        return False


# Get all the spaces information displayed on the portal
def get_spaces_info(driver: webdriver.Chrome):
    room_ids = []
    spaces = driver.find_elements(By.CLASS_NAME, "fc-cell-text")
    for space in spaces:
        parent_anchor_element = space.find_element(By.XPATH, "..")
        room_id = str(parent_anchor_element.get_attribute("href")).split("/")[-1]
        if space.text.split(" ")[0] in preferred_rooms:
            room_ids.insert(0, {"id": room_id, "is_preferred": True, "name": space.text})
        else:
            room_ids.append({"id": room_id, "is_preferred": False, "name": space.text})

    return room_ids


def reserve_space(driver: webdriver.Chrome, space_timeline: WebElement, start_time: str, max_bookable_slots, bookings_count):
    booked_slots = 0
    all_slots = space_timeline.find_elements(By.TAG_NAME, "a")
    for i in all_slots:
        if "s-lc-eq-avail" in str(i.get_attribute("class")).split(" ") and str(i.get_attribute("title")).startswith(start_time):
            # Not able to use i.click(), since it has so many overlays on top of it, so using JS to trigger click
            driver.execute_script("arguments[0].click();", i)
            bookings_count += 1

            # If the request is in process state, handling with while loop for every second
            counter = 0
            while counter < retry_count:
                try:
                    time.sleep(1)
                    booking_select_box = driver.find_element(By.ID, "bookingend_" + str(bookings_count))
                    select = Select(booking_select_box)
                    booked_slots = len(select.options)
                    start_time = str(select.options[-1].text).split(" ")[0]
                    break
                except NoSuchElementException as ex:
                    print("Request processing, Unable to access element: ", str(ex).split("}")[0])
                    counter += 1
                    continue

    return booked_slots, start_time, bookings_count


def quit_program(driver):
    driver.quit()
    return


class ReserveStudyRoom(unittest.TestCase):
    def setUp(self) -> None:
        self.driver = webdriver.Chrome()
        # self.driver.set_window_size(2500, 1600)

    def test_reserve_study_room(self) -> None:
        self.driver.get("https://studentcenters-gmu.libcal.com/spaces")

        dates = get_dates("custom")

        for date in dates:
            if not select_the_date(self.driver, date):
                return quit_program(self.driver)

            spaces = get_spaces_info(self.driver)
            booked_slots_per_day = bookings_count = 0
            start_time = "10:00am"
            for space in spaces:
                space_timeline = self.driver.find_element(
                    By.XPATH, "//td[contains(@class, 'fc-timeline-lane') and @data-resource-id='eid_" + space["id"] + "']"
                )
                print(space, space_timeline.get_attribute("data-resource-id"))
                booked_slots, start_time, bookings_count = reserve_space(
                    self.driver, space_timeline, start_time, max_bookable_slots_per_day - booked_slots_per_day, bookings_count
                )
                print("result", booked_slots, start_time)
                booked_slots_per_day += booked_slots
                if booked_slots_per_day > max_bookable_slots_per_day or bookings_count >= max_bookings:
                    print("Slots limit reached!")
                    break

            break

        # Implicit & Explicit wait functions doesn't work properly in python version of selenium
        # Instead using sleep
        time.sleep(4)

    def tearDown(self):
        self.driver.close()


if __name__ == "__main__":
    unittest.main()
