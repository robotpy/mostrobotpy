from typing import Iterable, ValuesView
import rich.progress
from datetime import datetime
import inspect

import rich.text

from .subproject import Subproject

def progress(
    sequence: ValuesView[Subproject],
) -> Iterable[Subproject]:

    taskname = inspect.stack()[1].function

    class NumTaskColumn(rich.progress.ProgressColumn):
        def render(self, task: rich.progress.Task) -> rich.text.Text:
            return rich.text.Text(f"{task.completed}/{task.total}", style="purple")

    current_hour = datetime.now().hour
    if 7 <= current_hour < (12 + 9):
        spinner_name = "earth"
    else:
        spinner_name = "moon"

    progress =  rich.progress.Progress(
        rich.progress.SpinnerColumn(spinner_name=spinner_name),
        rich.progress.TextColumn("[progress.description]{task.description}"),
        rich.progress.BarColumn(),
        NumTaskColumn(),
        rich.progress.TimeElapsedColumn(),
        redirect_stdout=True,
        redirect_stderr=True,
        # refresh_per_second=50
    )

    with progress:
        for item in progress.track(
            sequence, total=len(sequence)
        ):
            progress.update(progress.task_ids[0], description=f"{taskname} {item.name}")
            yield item

