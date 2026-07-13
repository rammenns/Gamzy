# FreeGamz

Hello, and welcome! **Gamzy** is a small desktop app that searches for you what temporary **free games** are on **Steam**, **Epic Games**, **GOG**, **itch.io** in one place, so you don't need to bother searching everywhere. In the next versions I'll try to make the app show what **free games** offers are on other platforms aswell.

## How to download

Check the **Releases** section and download the installer from there. Installing **Gamzy** is not complicated, it only needs a path towards where you wish the app to be installed and a checkbox if you want a **Desktop Shortcut**.

## How does it work

1. In background, a script is scrapping the internet to save the data of the free games offers
2. The UI shows you the platform from where the game was found, the name and poster of the game, all packaged in a card
3. Just click the card of the game you are interested in, and it will open a new web tab with that game you want to download
4. The "Hide" menu hides games from platforms you are not interested in and the "Silence" menu does the same but for desktop notifications

## Note

- For the script to function, it requiers internet conection
- At first after installing, the app will need a few moments to start showing the games

## Future improvements

- New platforms offers when the first 100% discount or giveaway will appear
- Anything else you would sugest and would make a diference

## Technology used

- Python
- PyQt5 (GUI)
- httpx, Requests and Beautifulsoup (webscrapping)
- asyncio (asyncron tasks)
- SQLite (local databases)
- winotify (desktop notifications)
- Inno Setup (Windows installer)
