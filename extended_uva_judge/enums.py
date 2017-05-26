class ProblemResponses:
    def __init__(self):
        raise NotImplementedError()

    # The program is correct and runs within the memory and time limits
    ACCEPTED = 'AC'

    # AE is different from book. I wanted a unique code.
    # The program is correct within an acceptable margin of error. Possibly an
    # extra space at the end of a line or an extra newline at the end of the
    # output.
    ACCEPTED_PRESENTATION_ERROR = 'AE'

    # The program yields the correct result but the outputs are not formatted
    # as per the specification.
    PRESENTATION_ERROR = 'PE'

    # The program yielded incorrect results for one or more of the judges
    # test cases.
    WRONG_ANSWER = 'WA'

    # Compilation of the submission has failed and the judge cannot execute
    # the submission. Compilation output should be supplied to the submitter.
    COMPILE_ERROR = 'CE'

    # The program failed to execute without exception. Exception output should
    # be supplied to the submitter.
    RUNTIME_ERROR = 'RE'

    # The program took too much time on one or more of the test cases.
    TIME_LIMIT_EXCEEDED = 'TL'

    # The program ran out of memory while attempting to execute upon the test
    # cases.
    MEMORY_LIMIT_EXCEEDED = 'ML'

    # The program tried to print an excessive amount of output while executing.
    # This can be indicative of a infinite loop or some similar situation.
    OUTPUT_LIMIT_EXCEEDED = 'OL'

    # The program contains some illegal system function such as fork or popen.
    RESTRICTED_FUNCTION = 'RF'

    # Not enough details were specified during the submission for the judge to
    # take action.
    SUBMISSION_ERROR = 'SE'
