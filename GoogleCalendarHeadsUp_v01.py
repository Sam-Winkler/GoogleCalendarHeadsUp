from __future__ import print_function

import datetime
import os.path

import sched
import time
import requests
import winsound
from tkinter import messagebox, Tk

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def main():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        scheduler = sched.scheduler(time.time, time.sleep)

        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        print(" ")
        print(" ")
        print("Next Event:")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
            return

        # Prints the start and name of the next 10 events
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            start = datetime.datetime.fromisoformat(str(start))
            timestamp = time.mktime(start.timetuple())
            if timestamp > time.time():
                print(" ")
                print(
                    datetime.datetime.strptime(str(start)[11:-9], "%H:%M").strftime(
                        "%I:%M %p"
                    ),
                    "---",
                    event["summary"],
                )

                # Schedule the task to run at a specific time
                specific_time = timestamp - 60
                scheduler.enterabs(specific_time, 1, call_warning, ())
                scheduler.run()

    except HttpError as error:
        print("An error occurred: %s" % error)


def call_warning():
    root = Tk()
    root.withdraw()  # Hide the main Tkinter window

    winsound.PlaySound(
        "military-alarm-129017.wav",
        winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP,
    )

    for i in range(29):
        # To update wifi ip address to specific elgato light, open light controller
        # and click on "advanced settings" button to bring up menu which displays
        # ip address
        requests.put(
            "http://192.168.1.94:9123/elgato/lights",
            json={
                "numberOfLights": 1,
                "lights": [{"on": i % 2, "brightness": 50, "temperature": 200}],
            },
        )
        time.sleep(0.2)

    messagebox.showinfo(
        title="Upcoming Video Call", message="Video Call Beginning in 1 Minute!"
    )

    winsound.PlaySound(None, winsound.SND_PURGE)

    root.destroy()  # Destroy the hidden Tkinter window


if __name__ == "__main__":
    main()
