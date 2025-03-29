class QuarterRangeArgMixin:
    """
    Adds year-quarter range arguments to Django management commands
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "year_q_from",
            type=str,
            help='XXXXqQ, where XXXX is the year, q is the literal "q" and Q is 1, 2, 3 or 4',
        )
        parser.add_argument(
            "year_q_to",
            type=str,
            help='XXXXqQ, where XXXX is the year, q is the literal "q" and Q is 1, 2, 3 or 4',
        )
