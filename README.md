# Eight Sleep Local Integration

**Home Assistant custom integration** for locally retrieving bed status from the [**free-sleep**](https://github.com/throwaway31265/free-sleep/tree/main) project

> **Disclaimer**: This integration is **unofficial** and not endorsed by Eight Sleep. It only communicates with a local endpoint served by [free-sleep](https://github.com/throwaway31265/free-sleep/tree/main). Use at your own risk.

## What Works

- **Local polling**: Fetch bed temperature, target temp, water level, priming status, and more.
- **Separate devices**: Each bed side is exposed as its own device in Home Assistant, with individual sensors.
- **Adjustable poll interval**: Configure the update interval (in seconds) via an options flow in Home Assistant.
- **Companion project**: Designed to work alongside [free-sleep](https://github.com/throwaway31265/free-sleep/tree/main).

## In Progress / Help Wanted
- Adjusting Temperatures
- Snoozing and Stopping Alarms
- Exposing health metrics – Waiting for upstream go ahead

## Installation (via HACS)

1. **Add Custom Repository**
    - In Home Assistant, go to **HACS > Integrations**.
    - Click the 3-dot menu in the top right and select **Custom repositories**.
    - Add this repository’s URL (`https://github.com/throwaway31265/free-sleep/tree/main` or whichever fork you’re using) with **Integration** as the category.

2. **Install the Integration**
    - In HACS, search for **“Eight Sleep Local”**.
    - Click **Install**.
    - Restart Home Assistant once the installation is complete.

3. **Add via Home Assistant UI**
    - Go to **Settings > Devices & Services**.
    - Click **+ Add Integration**, search for **Eight Sleep Local**, and install it.
    - Provide your **host** and **port** (where free-sleep is running).
    - Optionally configure the **poll/update interval** via the integration’s **Configure** menu.

## Configuration

1. **Initial Setup**
    - Host & Port: Enter the IP or hostname and port number of your local machine running free-sleep.
    - Poll Interval: By default, this integration polls every 30 seconds. You can change this by selecting the **Configure** option after setup.

2. **Sensors**
    - You’ll see sensors for **left** and **right** sides of the bed, including:
        - `currentTemperatureF`
        - `targetTemperatureF`
        - `secondsRemaining`
        - `isAlarmVibrating`
        - `isOn`

## Support & Issues

- For local endpoint details, see [**free-sleep**](https://github.com/throwaway31265/free-sleep/tree/main).
- This is a community-driven project. PRs, issues, and discussions welcome.
- **Note**: This integration is **not** affiliated with or supported by Eight Sleep.

