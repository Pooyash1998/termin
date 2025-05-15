import requests
from typing import Final
import logging
import bs4
from utils import is_date_within_n_days

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

"""
User agent string for looking for Termine.    
"""
USER_AGENT_STRING: Final = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
)

def number_to_month(number):
    month_dict = {
        "01": "January",
        "02": "February",
        "03": "March",
        "04": "April",
        "05": "May",
        "06": "June",
        "07": "July",
        "08": "August",
        "09": "September",
        "10": "October",
        "11": "November",
        "12": "December"
    }
    return month_dict.get(number, "Invalid Month")

def format_url_2(soup: bs4.BeautifulSoup, needle: str, form_options_position: int = 0):
    """ Find the form options and format a url for the appropriate entry on 
    the "Auswahl des Anliegens" page of the appointment finder.

    :param soup: bs4.Beautifulsoup to search for the right <h3><h3/> element.
    :param needle: String to search for in a <h3></h3> element.
    :param form_options_position: Some options on the page have multiple elements (students / family / employees, for example)
    """
    url_base = "https://termine.staedteregion-aachen.de/auslaenderamt/location?mdt=89&select_cnc=1"
    header_element = soup.find("h3", string=lambda s: needle in s if s else False)
    if header_element:
        next_sibling = header_element.find_next_sibling()
        if next_sibling:
            li_elements = next_sibling.find_all("li")
            cnc_id = li_elements[form_options_position].get("id").split("-")[-1] if li_elements else None
            url_2 = f"{url_base}&cnc-{cnc_id}=1"            
            logging.info(f"{f'{needle} has cnc id: ' + cnc_id}")
            return True, url_2
        else:
            return False, f"Sibling element to h3 with '{needle}' not found."
    else:
        logging.info(f"Element containing '{needle}' not found.")
        return False, f"Element containing '{needle}' not found."


def superc_termin(form_pos: int = 0):
    """ Check if appointments are available at the Außenstelle SuperC.
    
    param: form_pos: There are 3 Anliegen to select. 0 for students, 1 for family, 2 for employees. 
    """
    form_labels = {
        0: "RWTH Studenten",
    }
    
    form_label = form_labels[form_pos]
    logging.info(f"Checking SuperC appointments for: {form_label}")

    headers = {"User-Agent": USER_AGENT_STRING}
    session = requests.Session()
    session.headers.update(headers)

    url_1 = 'https://termine.staedteregion-aachen.de/auslaenderamt/select2?md=1'        
    url_2 = ''
    url_3 = 'https://termine.staedteregion-aachen.de/auslaenderamt/suggest'
    res_1 = session.get(url_1)

    # Get RWTH cnc id
    soup = bs4.BeautifulSoup(res_1.content, 'html.parser')         
    success, url_2 = format_url_2(soup, "Super C", form_pos)
    if success:
        res_2 = session.get(url_2)
    else:
        return False, url_2

    soup = bs4.BeautifulSoup(res_2.content, 'html.parser')
    loc = soup.find('input', {'name': 'loc'}).get('value')
    logging.info(f'{"Super C loc: " + loc}')

    payload = {'loc':str(loc), 'gps_lat': '55.77858', 'gps_long': '65.07867', 'select_location': 'Ausländeramt Aachen - Außenstelle RWTH auswählen'}
    res_3 = session.post(url_2, data=payload)
    res_4 = session.get(url_3)
    
    if "Kein freier Termin verfügbar" not in res_4.text:        
        
        # get exact termin date
        soup = bs4.BeautifulSoup(res_4.text, 'html.parser')
        div = soup.find("div", {"id": "sugg_accordion"})
        summary_tag = soup.find('summary', id='suggest_details_summary')
        
        if div:
            # logging.info(f'{"Appointment available now in SuperC!"}')
            logging.info(f"Appointments found for {form_label} at SuperC!")
            h3 = div.find_all("h3")
            # res = 'New appointments are available now\n'
            res = f'New appointments available for {form_label}:\n'
            for h in h3:
                res += h.text + '\n'             
            return True, res[:-1]
        elif summary_tag:
            summary_text = summary_tag.get_text(strip=True)
            logging.info(f'{"Appointment available now in SuperC!"}')            
            logging.info(f"Immediate availability for {form_label} at SuperC!")
            return True, f'{form_label}:\n{summary_text}'
        else:
            logging.info(f'{"Cannot find sugg_accordion! Possible new appointments are available now in SuperC!"}')                
            return False, "Cannot find sugg_accordion! Possible new appointments are available now"
    else:        
        logging.info(f"No appointments available for {form_label} at SuperC")       
        return False, f"No available slots for {form_label} at this time"

if __name__ == "__main__":
   superc_termin()