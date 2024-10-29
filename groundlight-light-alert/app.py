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

MAX_DAILY_TRIGGERS = 1
TIMER = 12
TRIGGER_INTERVAL_S = (
    int(os.getenv("TRIGGER_INTERVAL_S"))
    if os.getenv("TRIGGER_INTERVAL_S") is not None
    else 1
)
DETECTOR = os.getenv("SA_DETECTOR")

try:
    # pygame.mixer.init()
    pygame.mixer.init(buffer=4096, frequency=22050)
    sound_mixer = pygame.mixer.music.load("media/dog_barking.mp3")
except Exception as e:
    logger.error(f"Error initializing pygame: {e}")

def env_variables_set():
    return (
        TRIGGER_INTERVAL_S is not None
        and DETECTOR is not None
    )

trigger_times = []
def trigger_sound() -> None:
    global trigger_times
    # count how many times we've triggered in the last day
    last_day = time.time() - 86400 # seconds in a day
    recent_times = filter(lambda x: x > last_day, trigger_times)
    num_triggers = len(recent_times)
    if num_triggers >= MAX_DAILY_TRIGGERS:
        logger.info(f"Already triggered {num_triggers} times today. Not triggering sound")
        return
    else:
        trigger_times.append(time.time())
        logger.info("Triggering sound")
        try:
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            logger.error(f"Error playing sound: {e}")

def get_most_recent_iq(
    detector: Detector, num_queries: int = 100
) -> None | ImageQuery:
    # TODO Find it or we don't
    iqs = gl.list_image_queries(page_size=num_queries).results
    for iq in iqs:
        if iq.detector_id == detector.id:
            return iq
    logger.info(f"No image query found in most recent {num_queries} queries")
    return None


def do_loop(
    detector: Detector, yes_start_time: Optional[datetime]
) -> Tuple[Optional[datetime], bool]:
    """A single loop for the server. We see if there's a new image query result and if it's a YES, we start a timer."""
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

        elif now - yes_start_time >= TIMER: # We alarm if we don't get a no for TIMER seconds
            logger.info(
                f"Received yes for more than {TIMER} seconds. Triggering sound"
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
