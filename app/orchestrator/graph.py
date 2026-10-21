from langgraph.graph import StateGraph, END
from app.orchestrator.state import AgentState
from app.agents.scraper_agent import scrape_job
from app.agents.ats_scorer_agent import score_ats
from app.agents.tailor_agent import tailor_resume
from app.agents.cover_letter_agent import generate_cover_letter
from app.agents.scheduler_agent import schedule_followup

def check_scraping_status(state: AgentState):
    if state.get("error") or state.get("status") == "failed":
        return END
    return "ats_scorer"

def create_pipeline_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("scraper", scrape_job)
    workflow.add_node("ats_scorer", score_ats)
    workflow.add_node("tailor", tailor_resume)
    workflow.add_node("cover_letter", generate_cover_letter)
    workflow.add_node("scheduler", schedule_followup)

    workflow.set_entry_point("scraper")
    
    # Conditional edge on scraper success/failure
    workflow.add_conditional_edges(
        "scraper",
        check_scraping_status,
        {
            END: END,
            "ats_scorer": "ats_scorer"
        }
    )
    
    workflow.add_edge("ats_scorer", "tailor")
    workflow.add_edge("tailor", "cover_letter")
    workflow.add_edge("cover_letter", "scheduler")
    workflow.add_edge("scheduler", END)

    return workflow.compile()

pipeline_graph = create_pipeline_graph()
