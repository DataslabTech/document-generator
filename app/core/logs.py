"""Логування застосунку."""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:\t%(asctime)s\t%(name)s\t%(message)s",
)

logger = logging.getLogger("doc_gen_logger")
