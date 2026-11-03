"""Temporary original-client frame cap while the independent MC client loads."""
from observe_overwatch import ResearchProcess
from native_runtime_settings import temporary_render_settings

class StartupRenderBudget:
    def __init__(self):self.active={}

    def start(self,pid,settings,timeline=None):
        if not settings.get('startupRenderBudget',True) or pid in self.active:return
        memory=ResearchProcess(pid)
        context=temporary_render_settings(memory,pid,{'client.MaxFPS':30})
        try:before=context.__enter__()
        except (ValueError,KeyError) as error:
            memory.close()
            if isinstance(error,KeyError) or str(error) in ('Native quality value differs','Native quality setting type differs','Native setting registry bounds'):
                return  # Unsupported metadata is optional; no writes occurred.
            raise
        self.active[pid]=(memory,context,timeline)
        if timeline:timeline.mark('native_startup_frame_budget',fps=30,previous=before)

    def restore(self):
        for pid in list(self.active):
            memory,context,timeline=self.active.pop(pid)
            try:
                context.__exit__(None,None,None)
                if timeline:timeline.mark('native_startup_frame_budget_restored',pid=pid)
            finally:memory.close()

budget=StartupRenderBudget()
