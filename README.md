# Gateau Auto Bingo - Desktop Client

[![CI](https://github.com/k2bd/gateau-desktop/actions/workflows/ci.yml/badge.svg)](https://github.com/k2bd/gateau-desktop/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/k2bd/gateau-desktop/branch/main/graph/badge.svg?token=ROPL2MQDR3)](https://codecov.io/gh/k2bd/gateau-desktop)

# Development

In order to run this client against a locally running API and Firebase emulator, go into the Firebase Emulator dashboard and create a user, then join the game on the locally running version of the web app.

Then run the following, replacing ``YOUR_EMAIL`` and ``YOUR_PASSWORD`` with the email and password of the account created in the Firebase emulator, and ``ROOM_CODE`` with the room code you want to connect to:
```
FIREBASE_AUTH_EMULATOR_HOST=http://127.0.0.1:9099 python -m gateau_desktop --email=YOUR_EMAIL --password=YOUR_PASSWORD --room=ROOM_CODE --api=http://127.0.0.1:8011 --key=any-string
```
