from server import get_article_features, get_network_summary, search_fact_checks

print("--- Testing get_article_features ---")
print(get_article_features(0))

print("\n--- Testing get_network_summary ---")
# Using a placeholder graph_id for now; format is "{dataset_name}_{counter}"
print(get_network_summary("politifact_0"))

print("\n--- Testing error handling (non-existent IDs) ---")
print(get_article_features(999999999))
print(get_network_summary("nonexistent_id"))

print("\n--- Testing search_fact_checks ---")
results = search_fact_checks("The Eiffel Tower is located in Paris.", n_results=3)
for r in results:
    print(r)