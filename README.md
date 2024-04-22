# Monster Pickpocket

The scrapper is used to get the data for the Monsta Party RAM.  
[Monsta Party App](https://app.monsta.party/)

 **chromedriver** installed is required

For the scrapper you need to have the Chrome browser with Metamask extension already set up.  
This has been done manually. The password to the Metamask need to be added to the `.env` file in the root directory.

How to run the scrapper:
```shell
python scrapper.py
```

The data is saved into `<project-directory>/data/<current-date>`

Transform scrapped data for a given date assuming it is already saved:
```shell
python pickpocket.py -d 2024-04-22
```