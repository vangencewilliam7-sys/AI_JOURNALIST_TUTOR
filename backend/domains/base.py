from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseDomain(ABC):
    """
    Abstract base class defining the 6-Phase Agentic Chain.
    """

    @abstractmethod
    async def intake(self, expert_id: str) -> Dict[str, Any]:
        """
        Phase 2: Intake
        Generates the Day 1 icebreaker and initial strategy based on the expert's profile.
        """
        pass

    @abstractmethod
    async def generate_script(self, expert_id: str) -> Dict[str, Any]:
        """
        Phase 2 & Phase 6: Script Generation
        Generates the interview script for the current iteration based on the expert's profile and any identified homework gaps.
        """
        pass

    @abstractmethod
    async def live_turn(self, session_id: str, expert_answer: str, request_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Phase 3: Live Follow-up
        Classifies intent and generates the next conversational follow-up to dig deeper into the expert's answer.
        """
        pass

    @abstractmethod
    async def synthesize(self, session_id: str) -> Dict[str, Any]:
        """
        Phase 4: Post-Session Synthesis
        Takes the raw transcript of the session and extracts structured knowledge (persona, war stories, etc.).
        For the Tutor stream, this also extracts course modules, topics, and content.
        """
        pass

    @abstractmethod
    async def generate_homework(self, session_id: str) -> Dict[str, Any]:
        """
        Phase 5: Homework Generation
        Identifies "open loops" or missing knowledge gaps from the extracted data to form the homework ledger.
        """
        pass

    @abstractmethod
    async def flywheel_bridge(self, expert_id: str) -> Dict[str, Any]:
        """
        Phase 6: Day 2+ Flywheel Bridge
        Generates a trust-signal opener for the next session based on the completed homework ledger.
        """
        pass
