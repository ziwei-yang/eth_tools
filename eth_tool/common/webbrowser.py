#################################################
# Use selenium for fetching browser only data.
#################################################

import time
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import ui

from .logger import log, debug, error

def move_to_element(browser, el):
    # move_to_element() will raise error.
    # webdriver.ActionChains(browser).move_to_element(select_els[0]).perform()
    # Use javascript to achieve this.
    x = el.location['x']
    y = el.location['y']
    js = "window.scrollTo(" + str(x-100) + "," + str(y-100) + ")"
    browser.execute_script(js)

def render_with_firefox(url, **kwargs):
    verbose = (kwargs.get("verbose") != False)
    # See https://www.selenium.dev/selenium/docs/api/py/webdriver_firefox/selenium.webdriver.firefox.options.html
    firefox_options = webdriver.FirefoxOptions()
    if kwargs.get("headless") != False:
        firefox_options.headless = True
    firefox = webdriver.Firefox(options=firefox_options)
    firefox.set_window_size(1400, 900)
    # Navigate to url
    if verbose:
        debug("Render with firefox\n", url)
    firefox.get(url)

    render_t = kwargs.get('render_t') or 3
    if verbose:
        debug("Sleep", render_t, "after first load")
    time.sleep(render_t)

    post_func = kwargs.get('block')
    if post_func is None:
        html = firefox.page_source
        firefox.quit()
        return html

    # To manipulate browser:
    # See https://www.selenium.dev/documentation/en/webdriver/browser_manipulation/
    # To select by XPATH:
    # See https://www.guru99.com/xpath-selenium.html
    status_data = {} # Help post_func() to store any intermediate data.
    while True: # Endless trying if error happens.
        if verbose:
            debug("Process webpage with post_func\n", url)

        try:
            last_status_data = status_data.copy()
            ret, status_data = post_func(
                    firefox,
                    by=By, ui=ui, webdriver=webdriver,
                    status_data=status_data)
        except selenium.common.exceptions.StaleElementReferenceException:
            error("Have no idea why this happens, revert status data and try again.")
            status_data = last_status_data
            continue

        if status_data.get("error") is not None:
            error(status_data["error"])
        if ret == True:
            break
        if verbose:
            debug("Sleep", render_t, "until next round of post_func")
        time.sleep(render_t)

    html = firefox.page_source
    firefox.quit()
    return (html, status_data)
