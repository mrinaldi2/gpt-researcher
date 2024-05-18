from enum import Enum

from gpt_researcher import GPTResearcher
from colorama import Fore, Style

from .utils.views import print_agent_output

class ReportSource(Enum):
    External = 'internet'
    Internal = 'documents'

class ResearchAgent:
    def __init__(self):
        pass

    async def research(self, query: str, research_report: str = "research_report", parent_query: str = "", verbose=True, report_source: str = ReportSource.External.value):
        # Initialize the researcher
        researcher = GPTResearcher(query=query, report_source=report_source, report_type=research_report, parent_query=parent_query, verbose=verbose)
        # Conduct research on the given query
        await researcher.conduct_research()
        # Write the report
        report = await researcher.write_report()

        return report

    async def run_subtopic_research(self, parent_query: str, subtopic: str, verbose: bool = True, use_documents: bool = False):
        try:
            report_source = ReportSource.External.value if not use_documents else ReportSource.Internal.value
            report = await self.research(parent_query=parent_query, query=subtopic,
                                         research_report="subtopic_report", verbose=verbose, report_source=report_source)
        except Exception as e:
            print(f"{Fore.RED}Error in researching topic {subtopic}: {e}{Style.RESET_ALL}")
            report = None
        return {subtopic: report}

    async def run_initial_research(self, research_state: dict):
        task = research_state.get("task")
        query = task.get("query")
        report_source = ReportSource.Internal.value if task.get("use_documents") else ReportSource.External.value

        print_agent_output(f"Running initial research on the following query: {query}", agent="RESEARCHER")
        return {"task": task, "initial_research": await self.research(query=query, verbose=task.get("verbose"), report_source=report_source)}

    async def run_depth_research(self, draft_state: dict):
        task = draft_state.get("task")
        topic = draft_state.get("topic")
        parent_query = task.get("query")
        verbose = task.get("verbose")
        use_documents = task.get("use_documents")
        print_agent_output(f"Running in depth research on the following report topic: {topic}", agent="RESEARCHER")
        research_draft = await self.run_subtopic_research(parent_query, topic, verbose, use_documents)
        return {"draft": research_draft}
