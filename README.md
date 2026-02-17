This is a custom Garmin Connect watch face built for rowers and water sports enthusiasts in Nijmegen. It provides real-time, hyper-local environmental data directly on your wrist, helping you decide if it's safe to hit the water.

# Why this exists

Generic weather apps don't cut it for rowing in Nijmegen. We need to know:

1. Is the wind manageable (in combination with the water level)?
2. Is the water level good (I.E. no dike overflown or too low) ?
3. Should I wear my sunglasses? 
4. Will it be foggy in an hour?

This watch face solves that by pulling data from the best local sources available, not generic global models!

Safety Warning:
This watch face monitors the water level at Lobith. When the water level exceeds 1265cm, the Spiegelwaal begins to overflow/inundate. At this level, currents become unpredictable and rowing on the Spiegelwaal is considered unsafe, as the Spiegelwaal effectively becomes one with the Waal river where we do not row on.

## Features at a Glance

The display is designed to be easily readable:
* Top: Battery % and Date.
* Center: Time (Big and clear).
* Bottom Dashboard:
* Wind Timeline: Color-coded wind speed (Knots) for Now, +1h, +2h, and Tomorrow Morning (09:00).
* Colors behave like WindFinder: purple (windless, chill), blue (decent) → green (bad) → yellow (storm) → red (stay indoor).
^^ the rowing experience also depends on the water height, a higher water level = a worse experience since the winds are not stopped by the dikes.


* Precipitation: Expected rainfall for the next 2 hours (mm).
Water Level: Current height at Lobith (cm) with a trend indicator (`^` rising, `v` falling) compared to tomorrow's forecast.


Status Indicators: "SUN" or "FOG" alerts based on visibility and cloud cover. currently sun and fog detection is not the best :( 




# How the backend works

Instead of running a dedicated server (which costs money), this project uses GitHub Actions as a free backend.

1. The Brain (GitHub Actions): every hour, a workflow runs a Python script (`fetch_data.py`).


2. The Sources:
Weather: We query [Open-Meteo]() specifically for the KNMI Harmonie Arome model. This is the high-resolution Dutch weather model, which is significantly more accurate for local Dutch weather than others.

Water: We query the Rijkswaterstaat API for the "Lobith" station to get precise water heights from now and predicted levels in the near future.


3.  The script processes this data and saves a lightweight `data.json` file back to this repository.

4. The Watch: Your Garmin watch connects to your phone via Bluetooth, downloads that raw JSON file every hour via a GET request, and stores it in its memory. The watchface then takes this data and display all this data to the display.





# Build & Install Guide
Want to modify the code, add custom features or another background image? Do this!

# 1. Prerequisites

You need a few tools installed on your computer:

* Visual Studio Code
* Java Development Kit: Required for the Garmin compiler. (JDK 17 or 11 work).
* Garmin Connect IQ SDK Manager: 
* Open the SDK Manager, log in, and download the latest "Connect IQ SDK" and the device definitions for your specific watch.*



 # 2. Setup VSC

1. Open VS Code
2. Go to the Extensions tab
3. Search for and install Monkey C (by Garmin)
4. Open this repository folder in VS Code

# 3. Build & Run (Simulator)
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) and type `Monkey C: Build Current Project`.
2. Select your watch model.
3. Once built, go to the "Run and Debug" tab on the left and press the green "Play" button.
4. The simulator window should pop up.
* To test the data fetching, go to Simulation > Trigger Background Scheduled Event in the simulator menu, this forces the watch to download the `data.json` file.



# 4. Using real hardware

To get this on your actual wrist without publishing to the store:

1. Connect your Garmin watch to your computer via USB
2. In VS Code, run `Monkey C: Build for Device`
3. Select your specific watch model
4. This creates a `.prg` file in the `bin/` folder of the project
5. Drag and drop that `.prg` file into the `GARMIN/APPS/` folder on your watch's storage drive
6. Disconnect safely. The watch face should now be available in your watch's menu
^ (disclaimer my Macbook could not recognize my watch, but my Dell does.)


For questions or anything else, please reach out to me with my email: ruben.vlieger@ru.nl



To-do list:
Get better fog and sun detection 