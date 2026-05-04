# FreeGamz

Hello, and welcome! **FreeGamz** is a small desktop app that searches for you what temporary **free games** are on **Steam**, **Epic Games**, **GOG** in one place, so you don't need to bother searching everywhere. In the next versions I'll try to make the app show what **free games** offers are on other platforms aswell.

## How to download

Check the **Releases** section and download the installer from there. Installing **FreeGamz** is not complicated, it only needs a path towards where you wish the app to be installed and a checkbox if you want a **Desktop Shortcut**.

## How does it work

1. In background, a script is scrapping the internet to save the data of the free games offers
2. The UI shows you the platform from where the game was found, the name and poster of the game, all packaged in a card
3. Just click the card of the game you are interested in, and it will open a new web tab with that game you want to download

## Note

- For the script to function, it requiers internet conection
- At first after installing, the app will need a few moments to show the games

## Future improvements

- The app will send notifications when new games have been found
- Anything alse you would sugest and would make a diference

## The project sctructure

FreeGamz/ 
├── main.py
├── script.py
├── UI.py
├── games.db
├── gamzimgs/

## Technology used

- Pythn
- PyQt5 (GUI)
- Requests and Beautifulsoup (webscrapping)
- SQLite (local databases)
