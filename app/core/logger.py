import logging, sys

FMT = "%(asctime)s | %(levelname).1s | %(name)s | %(message)s"
logging.basicConfig(level=logging.INFO, format=FMT, stream=sys.stdout)
logger = logging.getLogger("news-shortform")
