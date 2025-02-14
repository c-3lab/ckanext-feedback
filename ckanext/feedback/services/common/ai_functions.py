import importlib
import logging

log = logging.getLogger(__name__)


def is_api_error(ng_reasons):
    ng_errors = ['RateLimitError', 'APIConnectionError', 'APIAuthenticationError']
    return not set(ng_reasons).isdisjoint(ng_errors)


def check_ai_comment(comment):
    MoralKeeperAI = importlib.import_module('moral_keeper_ai').MoralKeeperAI
    ai = MoralKeeperAI(timeout=120, max_retries=10, repeat=3)
    judgement, ng_reasons = ai.check(comment)
    if is_api_error(ng_reasons):
        log.exception('AI response failed. %s', ng_reasons)
    return judgement


def suggest_ai_comment(comment):
    if not comment:
        return None
    MoralKeeperAI = importlib.import_module('moral_keeper_ai').MoralKeeperAI
    ai = MoralKeeperAI(timeout=120, max_retries=10)
    return ai.suggest(comment)
