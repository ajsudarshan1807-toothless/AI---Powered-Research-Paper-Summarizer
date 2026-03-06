import datetime
from neo4j import GraphDatabase

# --- CONFIGURATION ---
URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "tN09dj1405")

# --- QUERIES ---

# 1. Count Nodes by Label
query_node_counts = """
MATCH (n)
RETURN distinct labels(n) as Label, count(*) as Total
ORDER BY Total DESC
"""

# 2. Count Relationships by Type
query_rel_counts = """
MATCH ()-[r]->()
RETURN type(r) as Type, count(*) as Total
ORDER BY Total DESC
"""

# 3. Get the 10 Most Recently Created Nodes
# We order by internal ID desc because Neo4j assigns IDs sequentially.
query_latest_nodes = """
MATCH (n)
RETURN labels(n) as Label, 
       properties(n) as Props
ORDER BY elementId(n) DESC
LIMIT 10
"""

# 4. Get the 10 Most Recently Created Relationships
query_latest_rels = """
MATCH (s)-[r]->(t)
RETURN coalesce(s.name, s.title, s.text, 'Node') as Source, 
       type(r) as RelType, 
       coalesce(t.name, t.title, t.text, 'Node') as Target,
       properties(r) as RelProps
ORDER BY elementId(r) DESC
LIMIT 10
"""

def print_separator(title):
    print(f"\n{'-'*10} {title} {'-'*10}")

def format_props(props):
    # Helper to clean up the property display so it fits on screen
    if not props:
        return "{}"
    # Pick a 'likely' main identifier to show, or just show the first few
    main_keys = ['name', 'title', 'text', 'year', 'source']
    
    # Try to find a readable key
    for k in main_keys:
        if k in props:
            val = str(props[k])
            # Truncate if too long
            return f"{k}: {val[:40]}..." if len(val) > 40 else f"{k}: {val}"
    
    # If no obvious key, take the first one
    k = list(props.keys())[0]
    return f"{k}: {str(props[k])[:30]}..."

def main():
    print(f"\n NEO4J LIVE STATUS REPORT")
    print(f" Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            with driver.session() as session:
                
                # --- SECTION 1: COUNTS ---
                print_separator("DATABASE SUMMARY")
                
                # Node Counts
                nodes_res = list(session.run(query_node_counts))
                if nodes_res:
                    print(f"{'Node Type':<30} | {'Count':<10}")
                    print("-" * 43)
                    for record in nodes_res:
                        label = ":".join(record["Label"]) if record["Label"] else "No Label"
                        print(f"{label:<30} | {record['Total']:,}")
                else:
                    print("  (No nodes found)")

                # Rel Counts
                print("")
                rels_res = list(session.run(query_rel_counts))
                if rels_res:
                    print(f"{'Relationship Type':<30} | {'Count':<10}")
                    print("-" * 43)
                    for record in rels_res:
                        print(f"{record['Type']:<30} | {record['Total']:,}")
                else:
                    print("  (No relationships found)")

                # --- SECTION 2: LATEST NODES ---
                print_separator("10 NEWEST NODES")
                latest_nodes = session.run(query_latest_nodes)
                print(f"{'Labels':<25} | {'Main Property Data'}")
                print("-" * 60)
                
                for record in latest_nodes:
                    lbl = ":".join(record["Label"])
                    props = format_props(record["Props"])
                    print(f"{lbl:<25} | {props}")

                # --- SECTION 3: LATEST RELATIONSHIPS ---
                print_separator("10 NEWEST RELATIONSHIPS")
                latest_rels = session.run(query_latest_rels)
                print(f"{'Source Node':<25} -> {'[RELATIONSHIP]':<15} -> {'Target Node'}")
                print("-" * 65)
                
                for record in latest_rels:
                    # Truncate names for cleaner table
                    src = (record['Source'][:23] + '..') if len(record['Source']) > 23 else record['Source']
                    trg = (record['Target'][:23] + '..') if len(record['Target']) > 23 else record['Target']
                    rel = record['RelType']
                    print(f"{src:<25} -> [{rel:<13}] -> {trg}")

                print("\n" + "=" * 60)
                print("Dashboard update complete.")

    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")

if __name__ == "__main__":
    main()