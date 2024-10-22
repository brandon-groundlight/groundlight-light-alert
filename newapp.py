from datetime import datetime
import logging
from typing import Optional, Tuple
import time

from groundlight import Groundlight, Detector, ImageQuery



gl = Groundlight()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trigger_sound() -> None:
    pass

def get_most_recent_iq(
    detector: Detector,
) -> None | ImageQuery:
    # TODO Find it or we don't
    iqs = gl.list_image_queries().results
    for iq in iqs:
        if iq.detector_id == detector.id:
            return iq
    return None


def do_loop(
    detector: Detector, yes_start_time: Optional[datetime]
) -> Tuple[Optional[datetime], bool]:
    """A single loop for the server. We get the result of the loop from grab_and_evaluate_image. Using that result,
    we determine if we've yes's for long enough to play a sound, keeping track if the sound is already playing
    We return the yes start time and the boolean of whether we are playing a sound"""
    result = get_most_recent_iq(detector)
    now = time.time()
    if result.label.value == "YES":
        logger.info("Received YES result!")
        if yes_start_time is None:
            logger.info("Starting yes timer....")
            yes_start_time = now

        elif now - yes_start_time >= 10: # We alarm if we don't get a no for 10 seconds
            logger.info(
                "Received yes for more than 10 seconds. Triggering sound"
            )
            trigger_sound()

    return yes_start_time


def start_server_loop() -> None:
    """Kick off the server loop, doing necesary setup like creating/getting the relevant detetor and continually
    checking for environment variables if they're not set"""
    detector = gl.get_or_create_detector(
        name="coffee_detector",
        query="Are there coffee grounds in the circle on the coffee maker?",
    )

    # initialize the next time we should run the loop as now
    next_run_time = time.time()
    yes_start_time = None
    playing_sound = False

    while True:
        now = time.time()
        if env_variables_set():
            if now >= next_run_time:
                yes_start_time, playing_sound = do_loop(
                    detector, yes_start_time, playing_sound
                )
                next_run_time = now + TRIGGER_INTERVAL_S
        else:
            logger.info("Environment variables not set. Sleeping....")
            next_run_time = now + 10
        time.sleep(min(1, next_run_time - now))


if __name__ == "__main__":
    logger.info("Starting loop")
    start_server_loop()
