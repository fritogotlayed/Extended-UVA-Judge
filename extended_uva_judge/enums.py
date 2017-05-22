class ProblemResponses:
    def __init__(self):
        raise NotImplementedError()

    ACCEPTED = 'AC'
    # AE is different from book. I wanted a unique code.
    ACCEPTED_PRESENTATION_ERROR = 'AE'
    PRESENTATION_ERROR = 'PE'
    WRONG_ANSWER = 'WA'
    COMPILE_ERROR = 'CE'
    RUNTIME_ERROR = 'RE'
    TIME_LIMIT_EXCEEDED = 'TL'
    MEMORY_LIMIT_EXCEEDED = 'ML'
    OUTPUT_LIMIT_EXCEEDED = 'OL'
    RESTRICTED_FUNCTION = 'RF'
    SUBMISSION_ERROR = 'SE'
