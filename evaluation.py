
import asyncio
import json
from collections import Counter
from typing import Dict, List
from agents.system import run_analysis_pipeline, TriageAgent

def load_json_data(file_path: str) -> dict:
    """Loads data from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

async def test_consistency(test_case: dict, num_runs: int = 5) -> Dict:
    """Test consistency by running the same case multiple times."""
    print(f"\n--- Testing Consistency for {test_case['ticket_id']} ({num_runs} runs) ---")
    
    # Run the same case multiple times
    results = []
    for i in range(num_runs):
        result = await run_analysis_pipeline(test_case)
        results.append({
            'queue': result.recommended_queue,
            'priority': result.priority,
            'run': i + 1
        })
        print(f"Run {i+1}: {result.recommended_queue} ({result.priority})")
    
    # Analyze consistency
    queues = [r['queue'] for r in results]
    priorities = [r['priority'] for r in results]
    
    queue_counts = Counter(queues)
    priority_counts = Counter(priorities)
    
    queue_consistency = len(queue_counts) == 1
    priority_consistency = len(priority_counts) == 1
    
    return {
        'ticket_id': test_case['ticket_id'],
        'queue_consistent': queue_consistency,
        'priority_consistent': priority_consistency,
        'queue_distribution': dict(queue_counts),
        'priority_distribution': dict(priority_counts),
        'most_common_queue': queue_counts.most_common(1)[0][0],
        'most_common_priority': priority_counts.most_common(1)[0][0]
    }

async def detailed_triage_analysis(test_case: dict, num_runs: int = 3) -> Dict:
    """Test triage agent consistency specifically."""
    print(f"\n--- Testing TriageAgent Consistency for {test_case['ticket_id']} ---")
    
    triage_input = f"Subject: {test_case['subject']}\n\nMessage: {test_case['message']}"
    
    results = []
    for i in range(num_runs):
        triage_result = await TriageAgent.run(triage_input)
        triage_analysis = triage_result.output
        results.append({
            'category': triage_analysis.category,
            'urgency': triage_analysis.urgency_score,
            'sentiment': triage_analysis.sentiment,
            'run': i + 1
        })
        print(f"Run {i+1}: {triage_analysis.category} | Urgency: {triage_analysis.urgency_score} | Sentiment: {triage_analysis.sentiment}")
    
    # Analyze consistency
    categories = [r['category'] for r in results]
    urgencies = [r['urgency'] for r in results]
    sentiments = [r['sentiment'] for r in results]
    
    return {
        'ticket_id': test_case['ticket_id'],
        'category_consistent': len(set(categories)) == 1,
        'urgency_consistent': len(set(urgencies)) == 1,
        'sentiment_consistent': len(set(sentiments)) == 1,
        'category_distribution': dict(Counter(categories)),
        'urgency_distribution': dict(Counter(urgencies)),
        'sentiment_distribution': dict(Counter(sentiments))
    }

async def evaluate_system():
    """Enhanced system evaluation with detailed analysis."""
    test_cases = load_json_data('data/test_cases.json')
    ground_truth = load_json_data('data/ground_truth.json')
    
    print("\n" + "="*50)
    print("      ENHANCED SYSTEM EVALUATION")
    print("="*50)
    
    # Basic accuracy testing
    routing_correct = 0
    category_correct = 0
    results_summary = []
    
    print("\n1. ACCURACY TESTING")
    print("-" * 30)
    
    for case in test_cases:
        case_id = case['ticket_id']
        truth = ground_truth[case_id]
        
        # Run full pipeline
        final_route = await run_analysis_pipeline(case)
        
        # Check routing accuracy
        routing_match = final_route.recommended_queue == truth['expected_queue']
        if routing_match:
            routing_correct += 1
        
        # Check category accuracy
        triage_input = f"Subject: {case['subject']}\n\nMessage: {case['message']}"
        triage_result = await TriageAgent.run(triage_input)
        triage_analysis = triage_result.output
        
        category_match = triage_analysis.category == truth['expected_category']
        if category_match:
            category_correct += 1
        
        results_summary.append({
            'ticket_id': case_id,
            'routing_match': routing_match,
            'category_match': category_match,
            'predicted_queue': final_route.recommended_queue,
            'expected_queue': truth['expected_queue'],
            'predicted_category': triage_analysis.category,
            'expected_category': truth['expected_category'],
            'reasoning': final_route.reasoning
        })
        
        status_route = "✓" if routing_match else "✗"
        status_category = "✓" if category_match else "✗"
        
        print(f"{case_id}: Route {status_route} | Category {status_category}")
        if not routing_match:
            print(f"  Expected: {truth['expected_queue']}, Got: {final_route.recommended_queue}")
        if not category_match:
            print(f"  Expected: {truth['expected_category']}, Got: {triage_analysis.category}")
    
    # Consistency testing
    print("\n2. CONSISTENCY TESTING")
    print("-" * 30)
    
    consistency_results = []
    
    # Test each case for consistency
    for case in test_cases:
        consistency_result = await test_consistency(case, num_runs=3)
        consistency_results.append(consistency_result)
    
    # Detailed triage analysis
    print("\n3. TRIAGE AGENT ANALYSIS")
    print("-" * 30)
    
    triage_consistency_results = []
    for case in test_cases:
        triage_result = await detailed_triage_analysis(case, num_runs=3)
        triage_consistency_results.append(triage_result)
    
    # Calculate metrics
    num_cases = len(test_cases)
    routing_accuracy = (routing_correct / num_cases) * 100
    category_accuracy = (category_correct / num_cases) * 100
    
    # Consistency metrics
    fully_consistent_cases = sum(1 for r in consistency_results 
                                if r['queue_consistent'] and r['priority_consistent'])
    queue_consistent_cases = sum(1 for r in consistency_results if r['queue_consistent'])
    
    consistency_rate = (fully_consistent_cases / num_cases) * 100
    queue_consistency_rate = (queue_consistent_cases / num_cases) * 100
    
    # Triage consistency metrics
    triage_fully_consistent = sum(1 for r in triage_consistency_results 
                                 if r['category_consistent'] and r['urgency_consistent'] and r['sentiment_consistent'])
    triage_category_consistent = sum(1 for r in triage_consistency_results if r['category_consistent'])
    
    triage_consistency_rate = (triage_fully_consistent / num_cases) * 100
    triage_category_consistency_rate = (triage_category_consistent / num_cases) * 100
    
    # Final comprehensive report
    print("\n" + "="*50)
    print("           COMPREHENSIVE REPORT")
    print("="*50)
    
    print(f"\n📊 ACCURACY METRICS:")
    print(f"   • Routing Accuracy: {routing_accuracy:.1f}% ({routing_correct}/{num_cases})")
    print(f"   • Category Accuracy: {category_accuracy:.1f}% ({category_correct}/{num_cases})")
    
    print(f"\n🔄 CONSISTENCY METRICS:")
    print(f"   • Full Consistency: {consistency_rate:.1f}% ({fully_consistent_cases}/{num_cases})")
    print(f"   • Queue Consistency: {queue_consistency_rate:.1f}% ({queue_consistent_cases}/{num_cases})")
    print(f"   • Triage Full Consistency: {triage_consistency_rate:.1f}% ({triage_fully_consistent}/{num_cases})")
    print(f"   • Triage Category Consistency: {triage_category_consistency_rate:.1f}% ({triage_category_consistent}/{num_cases})")
    
    print(f"\n🎯 PROBLEM AREAS:")
    incorrect_routes = [r for r in results_summary if not r['routing_match']]
    incorrect_categories = [r for r in results_summary if not r['category_match']]
    
    if incorrect_routes:
        print("   Routing Errors:")
        for error in incorrect_routes:
            print(f"     • {error['ticket_id']}: {error['expected_queue']} → {error['predicted_queue']}")
    
    if incorrect_categories:
        print("   Category Errors:")
        for error in incorrect_categories:
            print(f"     • {error['ticket_id']}: {error['expected_category']} → {error['predicted_category']}")
    
    inconsistent_cases = [r for r in consistency_results if not r['queue_consistent']]
    if inconsistent_cases:
        print("   Inconsistent Cases:")
        for case in inconsistent_cases:
            print(f"     • {case['ticket_id']}: {case['queue_distribution']}")
    
    print(f"\n✅ OVERALL SYSTEM HEALTH:")
    overall_score = (routing_accuracy + category_accuracy + consistency_rate) / 3
    if overall_score >= 90:
        health_status = "EXCELLENT 🟢"
    elif overall_score >= 80:
        health_status = "GOOD 🟡"
    elif overall_score >= 70:
        health_status = "FAIR 🟠"
    else:
        health_status = "POOR 🔴"
    
    print(f"   • Overall Score: {overall_score:.1f}%")
    print(f"   • System Health: {health_status}")
    
    print("\n" + "="*50)
    
    return {
        'routing_accuracy': routing_accuracy,
        'category_accuracy': category_accuracy,
        'consistency_rate': consistency_rate,
        'overall_score': overall_score,
        'results_summary': results_summary,
        'consistency_results': consistency_results
    }

if __name__ == "__main__":
    asyncio.run(evaluate_system())