"""
Class to hold original question store (from file),
and results of duplication detection.
"""

import dotsi  # type: ignore
import logging
import openpyxl
import os
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
import spacy_universal_sentence_encoder

# Get looger for this application
log = logging.getLogger(__name__)

# Load the spaCy model.
# Had to download separately, and doing via pyproject.toml file didn't seem to work.
# poetry run python -m spacy download en_core_web_md
# Didn't need to do this for the universal sentence encoder.
nlp = spacy_universal_sentence_encoder.load_model('en_use_lg')

class Question:
    """
    Question class.
    """

    def __init__(self, lid: int, question_text: str, answer: bool) -> None:
        """
        Question initialisation.
        Args:
            lid:            Legacy Id.
            question_text:  Question text (including ?).
            answer:         Expected response True=yes, False=no.
        Returns:
            Returns         None.
        """

        # Id of the source question.
        self.lid = lid

        # Raw question text.
        self.original_question = question_text
        # Normalise the string and convert to tokens.
        self.tokens = self.original_question.lower().split()
        # Check for possible negative sentiment.
        self.neg_sentiment = True if 'not' in self.tokens else False
        # Remove punctuation.
        self.tokens = [token.strip('?,.!') for token in self.tokens]
        # Remove common words that bias matching (stop words).
        self.tokens = [token for token in self.tokens if token not in list(STOP_WORDS)]

        # Reform tokens to processing string.
        self.question = ' '.join(self.tokens)

        # Expected answer, True=yes, False=no.
        self.answer = answer

        # Whether or not question has been the reference question yet.
        self.reference = False
        # Question statuses.
        self.unique = True
        self.duplicate = False
        # List of duplicates to this question.
        self.duplicates = []

class Question_Store:
    """
    Class for the store of questions.
    """

    def __init__(self, q_file: str, settings: dotsi.Dict) -> None:
        """
        Question_Store initialisation.
        Args:
            q_file:     Question file (Excel) containing questions.
            settings:   Applications settings.
        Returns:
            Returns None.
        """

        log.info("Initialising question store.")

        # Settings file.
        self.settings = settings

        # Initialise store.
        self._store = []
        self.num_q = 0
        self.status = self.settings.status.ST_NOQ


        # Load the workbook
        workbook = openpyxl.load_workbook(filename=q_file)

        # Select the active sheet
        sheet = workbook.active

        # Iterate through rows in the worksheet and extract question details.
        for row_num in range(2, sheet.max_row+1):
            q_text = sheet.cell(row=row_num, column=1).value
            q_answer = bool(sheet.cell(row=row_num, column=2).value)
            self._store.append(Question(row_num-1, q_text, q_answer))
            self.num_q += 1

        log.info(f"Number of questions read from file: {self.num_q}")

    def process(self) -> None:
        """
        Process questions.
        Look for duplicates questions.
        The rest will be unique questions.
        Args:
        Returns:
            Returns None.
        """

        log.info("Processing questions...")

        # Number of duplicate questions detected, and duplicates with errors.
        self.num_duplicates = 0
        self.num_negatives = 0

        # If only one question, nothing to test as questions unique.
        if self.num_q == 1:
            self.status = self.settings.status.ST_NOQ
            log.warning(f"Status: {self.status}")
            return

        # Else, process questions.
        for idx, q in enumerate(self._store[0:]):

            # Need to find the first reference question.
            # That is question that hasn't been compared against yet,
            # or is not already a duplicate question.
            if q.reference is True or q.duplicate is True:
                continue
            else:
                # Mark this question as being a reference question.
                q.reference = True
                log.debug(f"Ref. question, id: {q.lid}, Text: {q.original_question}, Tokens: {q.question}")

                # Need to find next question that isn't a duplicate.
                for idx2, q2 in enumerate(self._store[idx+1:]):
                    if q2.duplicate is True:
                        continue
                    else:
                        # Have 2 questions to compare now.
                        # Check similarity.
                        similarity = get_similarity(q.question, q2.question)
                        if similarity > self.settings.scores.SS_MATCH:
                            # Similarity score close enough for a match.
                            q2.unique = False
                            q2.duplicate = True
                            q.duplicates.append(q2)
                            self.num_duplicates += 1
                            if q2.neg_sentiment is False:
                                log.debug(f"DUPLICATE, id: {q2.lid}, Text: {q2.original_question}, Tokens: {q2.question}, similarity: {similarity :.3f}")
                            else:
                                log.debug(f"NEGATIVE SENTIMENT, id: {q2.lid}, Text: {q2.original_question}, Tokens: {q2.question}, similarity: {similarity :.3f}")
                                self.num_negatives += 1
                                # Check to make sure that the two questions have opposite answers,
                                # else negative sentiment might be wrong.
                                if q.answer == q2.answer:
                                    log.warning("Possible error in negative sentiment as answers not opposite.")
                        else:
                            # Not a match.
                            log.debug(f"Checked question, id: {q2.lid}, Text: {q2.original_question}, Tokens: {q2.question}, similarity: {similarity :.3f}")

    def results(self) -> None:
        """
        Output results of processing.
        Args:
        Returns:
            Returns None.
        """

        log.info("Generating results...")

        # Report on level of duplication detection.
        print("\n")
        print("*" * 80)
        print(f"Questions in orginal file           : {self.num_q}")
        print(f"Duplicate questions found           : {self.num_duplicates}")
        print(f"Negative sentiment questions found  : {self.num_negatives}")
        print(f"Duplicate questions (%)             : {self.num_duplicates / self.num_q * 100 :.1f}")
        print("*" * 80)

        # Go through Questions and create unique set.
        # Show the duplicates after the unique question if applicable.
        print("*" * 80)
        for idx, q in enumerate(self._store[0:]):
            if q.unique is True:
                print(f"({idx+1:05d}) {q.original_question} ({q.lid})")
                for op in q.duplicates:
                    # List duplicates if applicable.
                    if op.neg_sentiment is False:
                        print(f"\t({op.lid}) {op.original_question} DUPLICATE of ({q.lid})")
                    else:
                        print(f"\t({op.lid}) {op.original_question} DUPLICATE of ({q.lid}) [NEGATIVE]")
        print("*" * 80)

                        
def get_similarity(q1: str, q2: str) -> float:
    """
    Function to use ChatGPT to compare 2 questions for similarity.
    """

    # Process the input questions.
    proc_q1 = nlp(q1)
    proc_q2 = nlp(q2)

    # Determine the similarity score.
    return proc_q1.similarity(proc_q2)
