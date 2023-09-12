"""
Class to hold original question store (from csv file),
and results of duplication detection.
"""

import csv
import dotsi  # type: ignore
import logging
import os
import spacy
import spacy_universal_sentence_encoder
import time

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

    def __init__(self, lid: int, question_text: str, answer: str) -> None:
        """
        Question initialisation.
        Args:
            lid:            Legacy Id.
            question_text:  Question text (including ?).
            answer:         Expected response True=yes, False=no.
        Returns:
            Returns         None.
        """

        self.lid = lid
        self.question = question_text
        if answer == "yes":
            self.answer = True
        else:
            self.answer = False

        # Question statuses.

        # Whether or not question has been the reference question yet.
        self.reference = False
        self.unique = True
        self.duplicate = False
        self.duplicates = []
        self.opposite = False


class Question_Store:
    """
    Class for the store of questions.
    """

    def __init__(self, csv_file: str, settings: dotsi.Dict) -> None:
        """
        Question_Store initialisation.
        Args:
            csv_file:   CSV file containing questions.
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

        # Read CSV file and add to store.
        with open(csv_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Read the CSV file (one row per question).
                q_id = int(row['id'])
                q_text = row['question']
                q_answer = row['answer'].lower()
                self._store.append(Question(q_id, q_text, q_answer))
                self.num_q += 1

        log.info(f"Number of questions read from CSV file: {self.num_q}")

    def process(self) -> None:
        """
        Process questions.
        Look for duplicates, checking for opposite context questions.
        The rest will be unique questions.
        Args:
        Returns:
            Returns None.
        """

        log.info("Processing questions...")

        # Number of duplicate questions detected, and duplicates with errors.
        self.num_duplicates = 0

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
                log.debug(f"Ref. question, id: {q.lid}, Text: {q.question}")

                # Need to find next question that isn't a duplicate or an opposite.
                for idx2, q2 in enumerate(self._store[idx+1:]):
                    if q2.duplicate is True or q2.opposite is True:
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
                            # Just do a check that answers match as well.
                            if q.answer == q2.answer:
                                log.debug(f"DUPLICATE, id: {q2.lid}, Text: {q2.question}, similarity: {similarity :.3f}")
                            else:
                                # If questions considered a match and answers are opposite,
                                # then this is likely opposite question.
                                q2.opposite = True
                                log.debug(f"OPPOSITE, id: {q2.lid}, Text: {q2.question}, similarity: {similarity :.3f}")
                        else:
                            # Not a match.
                            log.debug(f"Checked question, id: {q2.lid}, Text: {q2.question}, similarity: {similarity :.3f}")

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
        print(f"Questions in orginal file      : {self.num_q}")
        print(f"Duplicate questions found      : {self.num_duplicates}")
        print(f"Duplicate questions (%)        : {self.num_duplicates / self.num_q * 100 :.1f}")
        print("*" * 80)

        # Go through Questions and create unique set.
        # Show the duplicates after the unique question if applicable.
        print("*" * 80)
        for idx, q in enumerate(self._store[0:]):
            if q.unique is True:
                print(f"({idx+1:05d}) {q.question} ({q.lid})")
                for op in q.duplicates:
                    # For duplicates indicate the opposite nature if applicable.
                    if op.opposite is False:
                        print(f"\t[{op.lid}] {op.question} ({op.lid})")
                    else:
                        print(f"\t[{op.lid}] {op.question} ({op.lid}) [Opposite]")
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