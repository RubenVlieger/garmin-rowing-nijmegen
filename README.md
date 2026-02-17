Here is the reformatted `README.md`. I have cleaned up the structure, converted your `***` sections into clear headers, and polished the text to sound professional but authentic (keeping your personal notes like the MacBook disclaimer).

I also added the link for Open-Meteo and formatted the wind/color section to be much easier to read at a glance.

---

# 🚣 Nijmegen Rowing Watch Face (Garmin)

This is a custom Garmin Connect watch face built for rowers and water sports enthusiasts in Nijmegen. It provides real-time, hyper-local environmental data directly on your wrist, helping you decide if it's safe to hit the water.

## Why this exists

Generic weather apps don't cut it for rowing in Nijmegen. To make a safe decision, we need to know:

1. **Is the wind manageable?** (Especially in combination with the current water level).
2. **Is the water level safe?** (Is the dike overflowing, or is it too low?).
3. **Should I wear sunglasses?**
4. **Will it be foggy soon?**

This watch face solves that by pulling data from the best *local* sources available, not generic global models.

> **⚠️ Safety Warning**
> This watch face monitors the water level at **Lobith**.
> * **Threshold:** When the water level exceeds **1265 cm**, the Spiegelwaal begins to overflow/inundate.
> * **Risk:** At this level, currents become unpredictable and the Spiegelwaal effectively becomes one with the Waal river. **Rowing on the Spiegelwaal is considered unsafe above this level.**
> 
> 

## Features at a Glance

The display is designed to be easily readable mid-stroke:

* **Top:** Battery % and Date.
* **Center:** Time (Big and clear).
* **Bottom Dashboard:**
* **Wind Timeline:** Color-coded wind speed (Knots) for **Now**, **+1h**, **+2h**, and **Tomorrow Morning (09:00)**.
* *Note:* The rowing experience depends heavily on water height; higher water = worse experience as the dikes stop blocking the wind.


* **Precipitation:** Expected rainfall for the next 2 hours (mm).
* **Water Level:** Current height at Lobith (cm) with a trend indicator (`^` rising, `v` falling) compared to tomorrow's forecast.
* **Status Indicators:** "SUN" or "FOG" alerts based on visibility and cloud cover. *(Currently, sun and fog detection is a work in progress).*



### Wind Color Guide (WindFinder Style)

| Color | Meaning |
| --- | --- |
| **Purple** | Windless / Chill |
| **Blue** | Decent |
| **Green** | Bad |
| **Yellow** | Storm |
| **Red** | Stay Inside |

## How the backend works

Instead of running a dedicated server (which costs money), this project uses **GitHub Actions** as a free backend.

1. **The Brain (GitHub Actions):** Every hour, a workflow runs a Python script (`fetch_data.py`).
2. **The Sources:**
* **Weather:** We query [Open-Meteo]() specifically for the **KNMI Harmonie Arome** model. This is the high-resolution Dutch weather model, significantly more accurate for our local weather than generic models.
* **Water:** We query the **Rijkswaterstaat** API for the "Lobith" station to get precise water heights for now and predicted levels in the near future.


3. **Processing:** The script processes this data and saves a lightweight `data.json` file back to this repository.
4. **The Watch:** Your Garmin watch connects to your phone via Bluetooth, downloads that raw JSON file every hour via a GET request, and updates the display.

---

## 🛠️ Build & Install Guide

Want to modify the code, add custom features, or change the background image? Follow these steps.

### 1. Prerequisites

You need a few tools installed on your computer:

* **Visual Studio Code** (VS Code).
* **Java Development Kit (JDK):** Required for the Garmin compiler. (JDK 17 or 11 work best).
* **Garmin Connect IQ SDK Manager:**
* Open the SDK Manager, log in, and download the latest "Connect IQ SDK".
* Download the device definitions for your specific watch (e.g., Fenix 7, Forerunner 965).



### 2. Setup VS Code

1. Open VS Code.
2. Go to the **Extensions** tab (left sidebar).
3. Search for and install **Monkey C** (by Garmin).
4. Open this repository folder in VS Code.

### 3. Build & Run (Simulator)

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) and type `Monkey C: Build Current Project`.
2. Select your watch model from the list.
3. Once built, go to the **Run and Debug** tab on the left and press the green "Play" button.
4. The simulator window should pop up.

* **Tip:** To test the data fetching, go to **Simulation > Trigger Background Scheduled Event** in the simulator menu. This forces the watch to download the `data.json` file immediately.

### 4. Using Real Hardware

To get this on your actual wrist without publishing to the store:

1. Connect your Garmin watch to your computer via USB.
2. In VS Code, run `Monkey C: Build for Device`.
3. Select your specific watch model.
4. This creates a `.prg` file in the `bin/` folder of the project.
5. Drag and drop that `.prg` file into the `GARMIN/APPS/` folder on your watch's storage drive.
6. Disconnect safely. The watch face should now be available in your watch's menu.

> **Hardware Note:** If you are on a Mac and it doesn't recognize your watch as a drive, try using a Windows machine or a different cable. (My MacBook wouldn't recognize it, but my Dell worked fine).

---

### 📝 To-Do List

* [ ] Improve the fog and sun detection logic.

### Contact

For questions or anything else, please reach out to me: **ruben.vlieger@ru.nl**