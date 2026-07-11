from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from .frozencombat import FrozenCombat
from .. import GameUpdateEvents
from ...ato.flightstate import InCombat, InFlight, FlightState
from ...ato.flightplans.formationattack import FormationAttackFlightPlan
from game.settings.settings import CombatResolutionMethod

if TYPE_CHECKING:
    from game.ato import Flight
    from ..simulationresults import SimulationResults


class AtIp(FrozenCombat):
    def __init__(self, freeze_duration: timedelta, flight: Flight) -> None:
        if not isinstance(flight.flight_plan, FormationAttackFlightPlan) or not isinstance(flight.state, InFlight):
            super().__init__(freeze_duration)
        elif self._other_flights_in_package_in_combat(flight) is not None:
            super().__init__(self._other_flights_in_package_in_combat(flight))
        else:
            freeze_duration = flight.flight_plan.tot_for_waypoint(self._unfreeze_state(flight).current_waypoint) - flight.flight_plan.tot_for_waypoint(flight.state.current_waypoint)
            super().__init__(freeze_duration)
        self.flight = flight

    def because(self) -> str:
        return f"{self.flight} is at its IP"

    def describe(self) -> str:
        return "at IP"

    def iter_flights(self) -> Iterator[Flight]:
        yield self.flight

    def resolve(
        self,
        results: SimulationResults,
        events: GameUpdateEvents,
        time: datetime,
        elapsed_time: timedelta,
        resolution_method: CombatResolutionMethod,
    ) -> None:
        logging.debug(
            f"{self.flight} attack on {self.flight.package.target} auto-resolved with "
            "mission failure but no losses"
        )
        assert isinstance(self.flight.state, InCombat)
        self.flight.state.exit_combat(
            events, time, elapsed_time, avoid_further_combat=True
        )
                    
    @staticmethod
    def _unfreeze_state(flight: Flight) -> InFlight:
        flight_state = flight.state
        assert isinstance(flight_state, InFlight)
        while flight_state.current_waypoint != flight.flight_plan.layout.split:
            flight_state = flight_state.next_waypoint_state()
            assert isinstance(flight_state, InFlight)
        return flight_state
        
    @staticmethod
    def _other_flights_in_package_in_combat(flight: Flight) -> InFlight:
        for package_flight in flight.package.flights:
            if package_flight.state.in_combat and isinstance(package_flight.state.combat, AtIp):
                return package_flight.state.combat.freeze_duration
                
        return None