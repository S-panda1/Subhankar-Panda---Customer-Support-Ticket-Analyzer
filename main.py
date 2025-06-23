import asyncio
import json
import argparse
from agents.system import run_analysis_pipeline

def load_test_cases(file_path: str) -> dict[str, dict]:
    """Loads test cases from a JSON file into a dictionary."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return {item['ticket_id']: item for item in data}

async def main():
    parser = argparse.ArgumentParser(description="Customer Support Ticket Analyzer")
    parser.add_argument(
        "ticket_id",
        type=str,
        help="The ID of the ticket to analyze (e.g., SUP-001)."
    )
    args = parser.parse_args()
    
    articles = load_test_cases('data/test_cases.json')
    ticket_to_process = articles.get(args.ticket_id)
    
    if not ticket_to_process:
        print(f"Error: Ticket with ID '{args.ticket_id}' not found.")
        return
        
    final_route = await run_analysis_pipeline(ticket_to_process)
    
    print("\n=======================================")
    print("          FINAL ROUTING")
    print("=======================================")
    print(f"Ticket ID: {ticket_to_process['ticket_id']}")
    print(final_route.model_dump_json(indent=2))
    print("=======================================\n")

if __name__ == "__main__":
    asyncio.run(main())