from datetime import datetime
import logging
import os
from typing import Optional, Tuple
import time

from groundlight import Groundlight, Detector, ImageQuery

from groundlight_light_alert import device_management as dm

gl = Groundlight()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_DAILY_TRIGGERS = int(os.getenv("MAX_DAILY_TRIGGERS")) if os.getenv("MAX_DAILY_TRIGGERS") else 5
TRIGGER_TIMER = int(os.getenv("TRIGGER_TIMER")) if os.getenv("TRIGGER_TIMER") else 5
POLLING_TIME_S = (
    int(os.getenv("POLLING_TIME_S"))
    if os.getenv("POLLING_TIME_S") is not None
    else 1
)
DETECTOR = os.getenv("DETECTOR")
SWITCH_ID = os.getenv("SWITCH_ID")

if not POLLING_TIME_S:
    raise ValueError("POLLING_TIME_S not set")
if not DETECTOR:
    raise ValueError("DETECTOR not set")
if not SWITCH_ID:
    raise ValueError("SWITCH_ID not set")

switch_manager = dm.SwitchManager(SWITCH_ID)

trigger_times = []
def trigger_sound() -> None:
    global trigger_times
    # count how many times we've triggered in the last day
    last_day = time.time() - 86400 # seconds in a day
    trigger_times = list(filter(lambda x: x > last_day, trigger_times))
    num_triggers = len(trigger_times)
    if num_triggers >= MAX_DAILY_TRIGGERS:
        logger.info(f"Already triggered {num_triggers} times today. Not triggering sound")
        return
    else:
        trigger_times.append(time.time())
        logger.info("Triggering sound")
        try:
            switch_manager.go_ham()
        except Exception as e:
            logger.error(f"Error playing sound: {e}")

def get_most_recent_iq(
    detector: Detector, num_queries: int = 100
) -> None | ImageQuery:
    # TODO Find it or we don't
    iqs = gl.list_image_queries(page_size=num_queries).results
    for iq in iqs:
        if iq.detector_id == detector.id and (iq.result.label == "YES" or iq.result.label == "NO"):
            return iq
    logger.info(f"No image query found in most recent {num_queries} queries")
    return None


def do_loop(
    detector: Detector, yes_start_time: Optional[datetime]
) -> Tuple[Optional[datetime], bool]:
    """A single loop for the server. We see if the most recent image query result is YES and if so we start a timer."""
    result = get_most_recent_iq(detector)
    now = time.time()
    logger.info(f"Current time: {now}")
    print(f"{result=}")
    logger.info(f"{result=}")
    if result and result.result.label == "YES":
        logger.info("Received YES result!")
        if yes_start_time is None:
            logger.info("Starting yes timer....")
            yes_start_time = now

        elif now - yes_start_time >= TRIGGER_TIMER: # We alarm if we don't get a no for TRIGGER_TIMER seconds
            logger.info(
                f"Received yes for more than {TRIGGER_TIMER} seconds. Triggering sound"
            )
            # NOTE: We don't time out the sound, it will play until the end
            trigger_sound()
            yes_start_time = None
    else:
        yes_start_time = None

    return yes_start_time


def start_server_loop() -> None:
    """Kick off the server loop, doing necesary setup like creating/getting the relevant detetor and continually
    checking for environment variables if they're not set"""
    try:
        detector = gl.get_detector(DETECTOR)
    except:
        logger.info("Detector not found, terminating process")
        exit(1)

    # initialize the next time we should run the loop as now
    next_run_time = time.time()
    yes_start_time = None

    while True:
        now = time.time()
        if now >= next_run_time:
            yes_start_time = do_loop(
                detector, yes_start_time
            )
            next_run_time = now + POLLING_TIME_S
        time.sleep(min(1, next_run_time - now))


if __name__ == "__main__":
    logger.info("Starting loop")
    start_server_loop()
