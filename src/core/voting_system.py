"""
Voting System for Blood on the Clocktower MVP
Handles nominations, voting, and execution logic
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum

from .game_state import Player


class VoteType(Enum):
    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"


@dataclass
class Vote:
    """Individual vote cast by a player"""

    player_name: str
    vote_type: VoteType
    is_ghost_vote: bool = False  # Dead players can vote once


@dataclass
class Nomination:
    """A nomination for execution"""

    nominator: str
    nominee: str
    votes: List[Vote]
    is_active: bool = True

    @property
    def yes_votes(self) -> int:
        return len([v for v in self.votes if v.vote_type == VoteType.YES])

    @property
    def no_votes(self) -> int:
        return len([v for v in self.votes if v.vote_type == VoteType.NO])

    @property
    def total_votes(self) -> int:
        return len([v for v in self.votes if v.vote_type != VoteType.ABSTAIN])


class VotingSystem:
    """Manages nominations and voting for executions"""

    def __init__(self, players: List[Player]):
        self.players = players
        self.nominations: List[Nomination] = []
        self.ghost_votes_used: Set[str] = set()  # Players who used ghost vote
        self.current_nomination: Optional[Nomination] = None

    def can_nominate(self, nominator_name: str, nominee_name: str) -> Tuple[bool, str]:
        """Check if a nomination is valid"""

        nominator = self._get_player(nominator_name)
        nominee = self._get_player(nominee_name)

        if not nominator:
            return False, f"Nominator {nominator_name} not found"

        if not nominee:
            return False, f"Nominee {nominee_name} not found"

        # Dead players cannot nominate
        if not nominator.is_alive():
            return False, "Dead players cannot nominate"

        # Cannot nominate dead players
        if not nominee.is_alive():
            return False, "Cannot nominate dead players"

        # Cannot nominate yourself
        if nominator_name.lower() == nominee_name.lower():
            return False, "Cannot nominate yourself"

        # Check if nominator already nominated today
        nominator_nominations = [
            n for n in self.nominations if n.nominator.lower() == nominator_name.lower()
        ]
        if nominator_nominations:
            return False, "Already nominated someone today"

        # Check if nominee already nominated today
        nominee_nominations = [
            n for n in self.nominations if n.nominee.lower() == nominee_name.lower()
        ]
        if nominee_nominations:
            return False, f"{nominee_name} already nominated today"

        return True, "Valid nomination"

    def create_nomination(
        self, nominator_name: str, nominee_name: str
    ) -> Optional[Nomination]:
        """Create a new nomination"""

        valid, reason = self.can_nominate(nominator_name, nominee_name)
        if not valid:
            return None

        nomination = Nomination(
            nominator=nominator_name, nominee=nominee_name, votes=[]
        )

        self.nominations.append(nomination)
        self.current_nomination = nomination

        return nomination

    def can_vote(self, player_name: str) -> Tuple[bool, str]:
        """Check if a player can vote on current nomination"""

        if not self.current_nomination:
            return False, "No active nomination"

        player = self._get_player(player_name)
        if not player:
            return False, f"Player {player_name} not found"

        # Check if already voted on this nomination
        existing_vote = next(
            (
                v
                for v in self.current_nomination.votes
                if v.player_name.lower() == player_name.lower()
            ),
            None,
        )
        if existing_vote:
            return False, "Already voted on this nomination"

        # Living players can always vote
        if player.is_alive():
            return True, "Can vote"

        # Dead players can vote once per game (ghost vote)
        if player_name.lower() not in self.ghost_votes_used:
            return True, "Can use ghost vote"

        return False, "Ghost vote already used"

    def cast_vote(self, player_name: str, vote_type: VoteType) -> bool:
        """Cast a vote on the current nomination"""

        can_vote, reason = self.can_vote(player_name)
        if not can_vote:
            return False

        player = self._get_player(player_name)
        is_ghost_vote = not player.is_alive()

        vote = Vote(
            player_name=player_name, vote_type=vote_type, is_ghost_vote=is_ghost_vote
        )

        self.current_nomination.votes.append(vote)

        # Mark ghost vote as used
        if is_ghost_vote:
            self.ghost_votes_used.add(player_name.lower())

        return True

    def close_voting(self) -> Optional[str]:
        """Close voting on current nomination and determine if execution occurs"""

        if not self.current_nomination:
            return None

        nomination = self.current_nomination
        self.current_nomination = None

        # Calculate execution threshold (half the living players, rounded up)
        alive_count = len([p for p in self.players if p.is_alive()])
        execution_threshold = (alive_count + 1) // 2

        # Check if nomination passes
        if nomination.yes_votes >= execution_threshold:
            return nomination.nominee
        else:
            return None

    def get_execution_threshold(self) -> int:
        """Get the number of votes needed for execution"""
        alive_count = len([p for p in self.players if p.is_alive()])
        return (alive_count + 1) // 2

    def can_start_nominations(self) -> Tuple[bool, str]:
        """Check if nominations can begin"""

        alive_players = [p for p in self.players if p.is_alive()]

        if len(alive_players) < 3:
            return False, "Need at least 3 alive players for nominations"

        return True, "Can start nominations"

    def get_eligible_nominators(self) -> List[str]:
        """Get players who can still nominate today"""

        alive_players = [p for p in self.players if p.is_alive()]
        nominators_used = {n.nominator.lower() for n in self.nominations}

        return [p.name for p in alive_players if p.name.lower() not in nominators_used]

    def get_eligible_nominees(self) -> List[str]:
        """Get players who can still be nominated today"""

        alive_players = [p for p in self.players if p.is_alive()]
        nominees_used = {n.nominee.lower() for n in self.nominations}

        return [p.name for p in alive_players if p.name.lower() not in nominees_used]

    def reset_for_new_day(self):
        """Reset voting system for a new day"""
        self.nominations.clear()
        self.current_nomination = None
        # Note: ghost_votes_used persists across days

    def get_voting_summary(self) -> str:
        """Get a summary of today's voting"""

        if not self.nominations:
            return "No nominations today"

        summary = f"Nominations today ({len(self.nominations)}):\n"

        for i, nom in enumerate(self.nominations, 1):
            summary += f"{i}. {nom.nominator} → {nom.nominee}: "
            summary += f"{nom.yes_votes} yes, {nom.no_votes} no"

            if nom.yes_votes >= self.get_execution_threshold():
                summary += " (EXECUTED)"
            else:
                summary += " (failed)"

            summary += "\n"

        return summary.strip()

    def _get_player(self, name: str) -> Optional[Player]:
        """Get player by name (case insensitive)"""
        for player in self.players:
            if player.name.lower() == name.lower():
                return player
        return None


# Simple majority voting for MVP
class SimpleMajorityVoting:
    """Simplified voting system for MVP - just tracks yes/no votes"""

    def __init__(self, players: List[Player]):
        self.players = players
        self.current_nominee: Optional[str] = None
        self.votes: Dict[str, VoteType] = {}

    def start_vote(self, nominee: str) -> bool:
        """Start voting on a nominee"""

        player = next(
            (p for p in self.players if p.name.lower() == nominee.lower()), None
        )
        if not player or not player.is_alive():
            return False

        self.current_nominee = nominee
        self.votes.clear()
        return True

    def cast_vote(self, voter: str, vote: VoteType) -> bool:
        """Cast a vote"""

        if not self.current_nominee:
            return False

        # Only alive players can vote in MVP
        player = next(
            (p for p in self.players if p.name.lower() == voter.lower()), None
        )
        if not player or not player.is_alive():
            return False

        self.votes[voter.lower()] = vote
        return True

    def get_result(self) -> Tuple[bool, int, int]:
        """Get voting result: (execute, yes_votes, no_votes)"""

        yes_votes = len([v for v in self.votes.values() if v == VoteType.YES])
        no_votes = len([v for v in self.votes.values() if v == VoteType.NO])

        alive_count = len([p for p in self.players if p.is_alive()])
        threshold = (alive_count + 1) // 2

        execute = yes_votes >= threshold

        return execute, yes_votes, no_votes

    def clear_vote(self):
        """Clear current vote"""
        self.current_nominee = None
        self.votes.clear()


if __name__ == "__main__":
    # Test voting system
    from .game_state import Player, PlayerStatus

    players = [
        Player("1", "Alice", 0, "Fortune Teller", PlayerStatus.ALIVE),
        Player("2", "Bob", 1, "Empath", PlayerStatus.ALIVE),
        Player("3", "Charlie", 2, "Chef", PlayerStatus.ALIVE),
        Player("4", "Diana", 3, "Washerwoman", PlayerStatus.ALIVE),
        Player("5", "Eve", 4, "Drunk", PlayerStatus.ALIVE),
        Player("6", "Frank", 5, "Poisoner", PlayerStatus.ALIVE),
        Player("7", "Grace", 6, "Imp", PlayerStatus.ALIVE),
    ]

    voting = VotingSystem(players)

    print("=== Testing Voting System ===")

    # Test nomination
    nom = voting.create_nomination("Alice", "Grace")
    if nom:
        print(f"Nomination created: {nom.nominator} → {nom.nominee}")

        # Test voting
        voting.cast_vote("Alice", VoteType.YES)
        voting.cast_vote("Bob", VoteType.YES)
        voting.cast_vote("Charlie", VoteType.NO)
        voting.cast_vote("Diana", VoteType.YES)

        print(f"Votes: {nom.yes_votes} yes, {nom.no_votes} no")
        print(f"Threshold: {voting.get_execution_threshold()}")

        # Close voting
        executed = voting.close_voting()
        print(f"Result: {executed} {'executed' if executed else 'not executed'}")

    print("\nTesting simple majority voting:")
    simple = SimpleMajorityVoting(players)
    simple.start_vote("Grace")
    simple.cast_vote("Alice", VoteType.YES)
    simple.cast_vote("Bob", VoteType.YES)
    simple.cast_vote("Charlie", VoteType.YES)
    simple.cast_vote("Diana", VoteType.NO)

    execute, yes, no = simple.get_result()
    print(
        f"Simple vote result: {yes} yes, {no} no → {
            'Execute' if execute else 'No execution'}")
