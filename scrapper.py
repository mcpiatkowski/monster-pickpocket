"""Monsta Party RAM scrapping module."""

import os
from dataclasses import dataclass, field
from io import StringIO

import pandas as pd
from dotenv import load_dotenv
from lxml import etree
from lxml.etree import HTMLParser, _Element
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


@dataclass
class Monsta:
    """Monster data."""

    pxp: int
    inactive: str
    earnings: float
    unclaimed_pxp: int
    id: int = field(compare=False)


def transform_earnings(earnings: str) -> float:
    """Transform earnings."""
    return float(earnings.split(" ")[0].replace(",", ""))


def transform_pxp(pxp: str) -> int:
    """Transform pxp."""
    return int(pxp.split(" ")[0].replace("(", ""))


def get_monster_info(monster_id: int, driver: WebDriver, parser: HTMLParser) -> Monsta:
    """Get monster info."""
    driver.get(f"https://app.monsta.party/#/robbery/{monster_id}")
    tree = etree.parse(StringIO(driver.page_source), parser)
    try:
        pxp_div: _Element = tree.xpath("//*[contains(@class, 'text-white font-bemio text-2xl mb-1 text-center')]")
        pxp = transform_pxp(pxp_div[0].text)

        divs: _Element = tree.xpath("//*[contains(@class, 'leading-6 mb-3')]")
        earnings = transform_earnings(divs[1].getchildren()[1].text)
        unclaimed_pxp = int(divs[0].getchildren()[1].text)
        inactive = divs[2].getchildren()[1].text

    except IndexError as error:
        pxp = None
        earnings = None
        inactive = None
        unclaimed_pxp = None
        print(error)

    return Monsta(id=monster_id, pxp=pxp, earnings=earnings, inactive=inactive, unclaimed_pxp=unclaimed_pxp)


def setup_chrome_options() -> ChromeOptions:
    """Set up chrome options."""
    chrome_options = ChromeOptions()
    user_data_dir = "/Users/michalpiatkowski/Library/Application Support/Google/Chrome"
    chrome_options.add_argument(f"user-data-dir={user_data_dir}")
    chrome_options.add_argument(r"--profile-directory=Default")

    return chrome_options


def unlock_metamask(password_element: WebElement, driver: WebDriver) -> None:
    """Unlock metamask."""
    password_element.send_keys(os.getenv("MONSTA_RAM"))
    print("Password entered.")
    submit_button = driver.find_element(By.CSS_SELECTOR, value="button[data-testid='unlock-submit']")
    submit_button.click()
    print("Unlocked successfully.")


def refresh_the_page(monsta_number: int, wait: WebDriverWait, driver: WebDriver) -> None:
    """Refresh the page.

    In case there is zero pxp the easiest way to get the next monster correctly is to refresh the page.
    """
    driver.get("https://www.google.com")
    driver.get(f"https://app.monsta.party/#/robbery/{monsta_number}")
    wait.until(ec.presence_of_element_located((By.XPATH, "//*[contains(@class, 'leading-6 mb-3')]")))


def write_to_parquet(monsters: pd.DataFrame) -> None:
    """Write scrapped data to parquet."""
    directory = f"data/{pd.to_datetime('now').strftime('%Y-%m-%d')}"
    if not os.path.exists(directory):
        os.mkdir(directory)
    else:
        print("Directory already exists.")

    monsters.to_parquet(f"{directory}/ram.parquet")


def execute_scraping(driver: WebDriver, parser: HTMLParser, range_start: int, range_end: int) -> None:
    """Execute scrapping."""
    _monsters = []
    monsta_number = range_start
    wait = WebDriverWait(driver, timeout=15)
    driver.get("chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html")

    element: WebElement = wait.until(ec.presence_of_element_located((By.ID, "password")))
    unlock_metamask(element, driver=driver)

    driver.get(f"https://app.monsta.party/#/robbery/{range_start}")
    wait.until(ec.presence_of_element_located((By.XPATH, "//*[contains(@class, 'leading-6 mb-3')]")))

    while monsta_number < range_end:
        _monsters.append(get_monster_info(monsta_number, driver=driver, parser=parser))

        if len(_monsters) == 1:
            monsta_number += 1
            print(_monsters[-1])
        elif _monsters[-1].pxp == 0:
            monsta_number += 1
            print(_monsters[-1])
            refresh_the_page(monsta_number, wait, driver=driver)
        elif _monsters[-1] != _monsters[-2]:
            monsta_number += 1
            print(_monsters[-1])
        else:
            _monsters.pop(-1)

    monsters: pd.DataFrame = pd.DataFrame(_monsters)
    print(monsters.head())

    write_to_parquet(monsters)


if __name__ == "__main__":
    load_dotenv()
    _parser: HTMLParser = etree.HTMLParser()
    _chrome_options: ChromeOptions = setup_chrome_options()
    _driver: WebDriver = webdriver.Chrome(options=_chrome_options)

    try:
        execute_scraping(_driver, _parser, range_start=0, range_end=9999)
    finally:
        _driver.quit()
