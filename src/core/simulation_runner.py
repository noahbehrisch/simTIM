import threading
import traceback
from collections.abc import Callable
from typing import Any

from src.core.simulation_orchestrator import SimulationOrchestrator, run_variable_scenarios


class SimulationRunner:
    """Wraps SimulationOrchestrator with threading and callbacks. Async for GUI, sync for CLI."""

    def __init__(
        self,
        on_progress: Callable[[int, int], None] | None = None,
        on_complete: Callable[[Any], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ):
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_error = on_error
        self._thread: threading.Thread | None = None
        self._result: Any = None

    @property
    def result(self) -> Any:
        return self._result

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def run_async(self, **kwargs) -> None:
        def _run():
            try:
                orchestrator = SimulationOrchestrator(
                    progress_callback=self.on_progress,
                    **kwargs,
                )
                self._result = orchestrator.run()
                if self.on_complete:
                    self.on_complete(self._result)
            except Exception as e:
                error_msg = str(e)
                print(f"\n🚨 SIMULATION ERROR: {error_msg}")
                traceback.print_exc()
                if self.on_error:
                    self.on_error(error_msg)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def run_scenarios_async(self, **kwargs) -> None:
        def _run():
            try:
                self._result = run_variable_scenarios(
                    progress_callback=self.on_progress,
                    **kwargs,
                )
                if self.on_complete:
                    self.on_complete(self._result)
            except Exception as e:
                error_msg = str(e)
                print(f"\n🚨 SIMULATION ERROR: {error_msg}")
                traceback.print_exc()
                if self.on_error:
                    self.on_error(error_msg)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def run_sync(self, **kwargs) -> Any:
        orchestrator = SimulationOrchestrator(progress_callback=self.on_progress, **kwargs)
        self._result = orchestrator.run()
        if self.on_complete:
            self.on_complete(self._result)
        return self._result

    def run_scenarios_sync(self, **kwargs) -> Any:
        self._result = run_variable_scenarios(progress_callback=self.on_progress, **kwargs)
        if self.on_complete:
            self.on_complete(self._result)
        return self._result
