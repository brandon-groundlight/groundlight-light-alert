from datetime import datetime
import logging
import os
from typing import Optional, Tuple
import time
import pygame

from groundlight import Groundlight, Detector, ImageQuery



gl = Groundlight()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TRIGGER_INTERVAL_S = (
    int(os.getenv("TRIGGER_INTERVAL_S"))
    if os.getenv("TRIGGER_INTERVAL_S") is not None
    else 3
)
DETECTOR = os.getenv("SA_DETECTOR")

pygame.mixer.init()
sound_mixer = pygame.mixer.Sound("media/dog_barking.mp3") # TODO

def env_variables_set():
    return (
        TRIGGER_INTERVAL_S is not None
        and DETECTOR is not None
    )

def trigger_sound() -> None:
    logger.info("Triggering sound")
    sound_mixer.play()

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
    """A single loop for the server. We see if there's a new image query result and if it's a YES, we start a timer."""
    result = get_most_recent_iq(detector)
    now = time.time()
    if result.result.label == "YES":
        logger.info("Received YES result!")
        if yes_start_time is None:
            logger.info("Starting yes timer....")
            yes_start_time = now

        elif now - yes_start_time >= 10: # We alarm if we don't get a no for 10 seconds
            logger.info(
                "Received yes for more than 10 seconds. Triggering sound"
            )
            # NOTE: We don't time out the sound, it will play until the end
            trigger_sound()

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
        if env_variables_set():
            if now >= next_run_time:
                yes_start_time = do_loop(
                    detector, yes_start_time
                )
                next_run_time = now + TRIGGER_INTERVAL_S
        else:
            logger.info("Environment variables not set. Sleeping....")
            next_run_time = now + 10
        time.sleep(min(1, next_run_time - now))


if __name__ == "__main__":
    logger.info("Starting loop")
    start_server_loop()
