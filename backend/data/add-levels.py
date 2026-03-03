import json
import re
from collections import Counter

INPUT_FILE = "Rag-db.json"  # Your input file with the concepts
OUTPUT_FILE = "final-chunks.json"

# ==========================
# DOMAIN/SUBDOMAIN MAPPING
# ==========================
DOMAIN_MAPPING = {
    # Programming Fundamentals
    "Syntax and semantics": ("programming_fundamentals", "language_basics"),
    "Primitive and reference data types": ("programming_fundamentals", "language_basics"),
    "Control flow statements (if-else, loops, switch)": ("programming_fundamentals", "language_basics"),
    "Functions and parameters": ("programming_fundamentals", "language_basics"),
    "Variable scope (block vs function)": ("programming_fundamentals", "scope_memory"),
    "Closures basics": ("programming_fundamentals", "scope_memory"),
    "Hoisting (var vs let/const)": ("programming_fundamentals", "scope_memory"),
    "Classes and objects": ("programming_fundamentals", "oop"),
    "Inheritance and polymorphism basics": ("programming_fundamentals", "oop"),
    "Encapsulation and abstraction": ("programming_fundamentals", "oop"),
    "Try-catch / error handling mechanisms": ("programming_fundamentals", "error_handling"),
    "Event loop intuition": ("programming_fundamentals", "async"),
    "Promises and chaining": ("programming_fundamentals", "async"),
    "async/await syntax and usage": ("programming_fundamentals", "async"),
    "Blocking vs non-blocking operations": ("programming_fundamentals", "async"),
    "Arrow functions and lexical this": ("programming_fundamentals", "javascript_advanced"),
    "Destructuring assignment": ("programming_fundamentals", "javascript_advanced"),
    "Template literals and string interpolation": ("programming_fundamentals", "javascript_advanced"),
    "Spread and rest operators": ("programming_fundamentals", "javascript_advanced"),
    
    # Code Quality
    "Naming conventions and clean code principles": ("code_quality", "readability"),
    "Comments and documentation best practices": ("code_quality", "readability"),
    "Writing maintainable code principles": ("code_quality", "readability"),
    "Basic refactoring techniques (extract method, rename)": ("code_quality", "refactoring"),
    "Modular code and single responsibility principle": ("code_quality", "modularization"),
    "Code review process and benefits": ("code_quality", "process"),
    "Version Control (Git) and Branching": ("code_quality", "version_control"),
    "Technical Debt intuition": ("code_quality", "architecture"),
    "Error Handling and Resilience": ("code_quality", "reliability"),
    
    # Data Structures
    "Time complexity intuition (Big-O basics)": ("data_structures", "complexity"),
    "Space complexity intuition": ("data_structures", "complexity"),
    "Arrays and common operations": ("data_structures", "core_structures"),
    "Strings manipulation basics": ("data_structures", "core_structures"),
    "Hash maps / dictionaries / objects": ("data_structures", "core_structures"),
    "Stacks and real-world use cases": ("data_structures", "core_structures"),
    "Queues and real-world use cases": ("data_structures", "core_structures"),
    "Basic recursion patterns": ("data_structures", "core_structures"),
    "Tree basics (binary tree intuition)": ("data_structures", "core_structures"),
    "Set data structure and uniqueness": ("data_structures", "core_structures"),
    "Map vs Object differences": ("data_structures", "core_structures"),
    
    # Backend
    "REST principles and constraints": ("backend", "api_basics"),
    "HTTP methods (GET, POST, PUT, DELETE)": ("backend", "api_basics"),
    "HTTP status codes categories": ("backend", "api_basics"),
    "JSON structure and usage": ("backend", "api_basics"),
    "Request-response lifecycle": ("backend", "api_basics"),
    "Request handling flow on server": ("backend", "server_side"),
    "Middleware concept and examples": ("backend", "server_side"),
    "Basic routing in web frameworks": ("backend", "server_side"),
    "Environment variables and config management": ("backend", "server_side"),
    "API versioning strategies": ("backend", "api_design"),
    "Query parameters vs path parameters": ("backend", "api_design"),
    "CORS (Cross-Origin Resource Sharing) basics": ("backend", "security"),
    "Stateless vs stateful servers": ("backend", "architecture"),
    "Rate limiting implementation intuition": ("backend", "security"),
    
    # Security
    "JWT concept and structure": ("security", "auth"),
    "Session-based vs token-based authentication": ("security", "auth"),
    "Basic authorization vs authentication": ("security", "auth"),
    "OAuth 2.0 flow intuition": ("security", "auth"),
    "Refresh tokens purpose": ("security", "auth"),
    "Input validation importance": ("security", "common_attacks"),
    "SQL injection awareness and prevention": ("security", "common_attacks"),
    "XSS (Cross-Site Scripting) basics": ("security", "common_attacks"),
    "CSRF (Cross-Site Request Forgery) awareness": ("security", "common_attacks"),
    "Password hashing and salting": ("security", "crypto"),
    "HTTPS and TLS basics": ("security", "crypto"),
    "Secure random number generation basics": ("security", "crypto"),
    
    # Database
    "Tables, rows, columns": ("database", "relational"),
    "Primary key and foreign key": ("database", "relational"),
    "Basic JOIN types intuition": ("database", "relational"),
    "ACID properties intuition": ("database", "relational"),
    "Database indexing purpose and trade-offs": ("database", "indexing"),
    "Why indexing improves query speed": ("database", "performance"),
    "Basic query optimization tips": ("database", "performance"),
    "When and why to use caching": ("database", "performance"),
    "Explain plan / query execution basics": ("database", "performance"),
    "Simple schema design principles": ("database", "modeling"),
    "Normalization basics (1NF-3NF intuition)": ("database", "modeling"),
    "Schema design trade-offs (denormalization)": ("database", "modeling"),
    "NoSQL vs SQL when to choose (fresher view)": ("database", "modeling"),
    "Document database basics (MongoDB intuition)": ("database", "nosql"),
    "Database replication basics": ("database", "architecture"),
    
    # System Design
    "Designing a simple CRUD application": ("system_design", "basic_features"),
    "Designing user authentication flow": ("system_design", "basic_features"),
    "Designing a file upload feature": ("system_design", "basic_features"),
    "Designing a notification system (simple)": ("system_design", "case_studies"),
    "Vertical vs horizontal scaling": ("system_design", "scaling"),
    "Load balancer basics and purpose": ("system_design", "scaling"),
    "Caching concept and benefits": ("system_design", "scaling"),
    "CDN (Content Delivery Network) purpose": ("system_design", "scaling"),
    
    # DevOps
    "What is Docker and containers": ("devops", "containers"),
    "CI/CD pipeline basics": ("devops", "ci_cd"),
    "Deployment pipeline intuition": ("devops", "deployment"),
    "GitHub Actions workflow basics": ("devops", "ci_cd"),
    "Basic monitoring and alerting": ("devops", "monitoring"),
    "Serverless functions (AWS Lambda basics)": ("devops", "serverless"),
    "Cloud basics (AWS/GCP/Azure free tier intuition)": ("devops", "cloud"),
    
    # Software Engineering
    "Step-by-step bug fixing approach": ("software_engineering", "debugging"),
    "Reading and interpreting logs": ("software_engineering", "debugging"),
    "Reproducing issues reliably": ("software_engineering", "debugging"),
    "Browser dev tools for debugging": ("software_engineering", "debugging"),
    "Rubber duck debugging technique": ("software_engineering", "debugging"),
    "Breaking down ambiguous problems": ("software_engineering", "problem_solving"),
    "Identifying performance bottlenecks": ("software_engineering", "performance"),
    "Manual vs automated testing mindset": ("software_engineering", "testing"),
    "Testing levels (Unit, Integration, E2E)": ("software_engineering", "testing"),
    "Unit testing basics and why it matters": ("software_engineering", "testing"),
    "Documentation types and value": ("software_engineering", "documentation"),
    "README and inline documentation importance": ("software_engineering", "documentation"),
    "Linters and formatters (ESLint, Prettier)": ("software_engineering", "tools"),
    "Console logging best practices": ("software_engineering", "practices"),
    "Pair programming benefits": ("software_engineering", "practices"),
    "Agile and Sprint basics": ("software_engineering", "agile"),
    "Agile and Scrum basics for freshers": ("software_engineering", "agile"),
    "Sprint planning and daily standups": ("software_engineering", "agile"),
    
    # Soft Skills
    "Asking good questions in meetings": ("soft_skills", "communication"),
    "Handling imposter syndrome": ("soft_skills", "career_growth"),
    "Using AI coding assistants responsibly (2026 view)": ("soft_skills", "tools"),
    "AI in software development trends for freshers": ("soft_skills", "trends"),
    
    # Distributed Systems
    "Retry strategies with backoff & jitter": ("distributed_systems", "reliability"),
    "Circuit breakers and bulkheads": ("distributed_systems", "reliability"),
    "Dead letter queues (DLQ)": ("distributed_systems", "messaging"),
    "Exactly-once vs at-least-once delivery": ("distributed_systems", "messaging"),
    "Saga pattern": ("distributed_systems", "messaging"),
    "Outbox pattern": ("distributed_systems", "messaging"),
    "Request tracing (correlation IDs)": ("distributed_systems", "observability"),
    
    # Observability
    "Structured logging": ("observability", "logging"),
    "Centralized logs (ELK stack)": ("observability", "logging"),
    "Distributed tracing (OpenTelemetry)": ("observability", "tracing"),
}

# ==========================
# SUBDOMAIN-BASED LEVEL MAPPING
# ==========================
LEVEL_MAPPING = {
    # L1 - Beginner level subdomains
    ("programming_fundamentals", "language_basics"): "L1",
    ("programming_fundamentals", "scope_memory"): "L1",
    ("programming_fundamentals", "oop"): "L1",
    ("programming_fundamentals", "error_handling"): "L1",
    
    ("data_structures", "core_structures"): "L1",
    ("data_structures", "complexity"): "L1",
    
    ("backend", "api_basics"): "L1",
    ("backend", "server_side"): "L1",
    
    ("database", "relational"): "L1",
    ("database", "modeling"): "L1",
    
    ("security", "common_attacks"): "L1",
    
    ("system_design", "basic_features"): "L1",
    ("system_design", "case_studies"): "L1",
    
    ("devops", "containers"): "L1",
    ("devops", "ci_cd"): "L1",
    ("devops", "deployment"): "L1",
    ("devops", "cloud"): "L1",
    
    ("code_quality", "readability"): "L1",
    ("code_quality", "refactoring"): "L1",
    ("code_quality", "modularization"): "L1",
    ("code_quality", "process"): "L1",
    ("code_quality", "version_control"): "L1",
    
    ("software_engineering", "debugging"): "L1",
    ("software_engineering", "testing"): "L1",
    ("software_engineering", "documentation"): "L1",
    ("software_engineering", "tools"): "L1",
    ("software_engineering", "practices"): "L1",
    ("software_engineering", "agile"): "L1",
    
    ("soft_skills", "communication"): "L1",
    ("soft_skills", "career_growth"): "L1",
    ("soft_skills", "tools"): "L1",
    ("soft_skills", "trends"): "L1",
    
    # L2 - Intermediate level subdomains
    ("programming_fundamentals", "async"): "L2",
    ("programming_fundamentals", "javascript_advanced"): "L2",
    
    ("backend", "api_design"): "L2",
    ("backend", "security"): "L2",
    ("backend", "architecture"): "L2",
    
    ("database", "indexing"): "L2",
    ("database", "performance"): "L2",
    ("database", "nosql"): "L2",
    ("database", "architecture"): "L2",
    
    ("security", "auth"): "L2",
    ("security", "crypto"): "L2",
    
    ("system_design", "scaling"): "L2",
    
    ("devops", "monitoring"): "L2",
    ("devops", "serverless"): "L2",
    
    ("code_quality", "architecture"): "L2",
    ("code_quality", "reliability"): "L2",
    
    ("software_engineering", "problem_solving"): "L2",
    ("software_engineering", "performance"): "L2",
    
    ("observability", "logging"): "L2",
    
    # L3 - Advanced level subdomains
    ("distributed_systems", "reliability"): "L3",
    ("distributed_systems", "messaging"): "L3",
    ("distributed_systems", "observability"): "L3",
    
    ("observability", "tracing"): "L3",
}

# ==========================
# CREATE CHUNKS
# ==========================

def create_chunks(concepts):
    """Convert concepts to chunks with metadata"""
    chunks = []
    missing_domains = set()
    missing_levels = set()
    
    for i, concept in enumerate(concepts):
        concept_name = concept["concept"]
        
        # Get domain and subdomain from mapping
        if concept_name not in DOMAIN_MAPPING:
            missing_domains.add(concept_name)
            domain, subdomain = ("unknown", "unknown")
        else:
            domain, subdomain = DOMAIN_MAPPING[concept_name]
        
        # Get level based on subdomain
        level = LEVEL_MAPPING.get((domain, subdomain))
        if not level:
            missing_levels.add(f"{domain}/{subdomain}")
            level = "L1"  # Default to L1 if not found
        
        # Create ID
        concept_id = concept_name.lower()
        concept_id = re.sub(r'[^a-z0-9]+', '_', concept_id)
        concept_id = concept_id.strip('_')
        chunk_id = f"concept_{i:04d}_{concept_id}"
        
        # Format the text
        text_parts = [f"Concept: {concept_name}\n"]
        text_parts.append(f"\nExplanation:\n{concept['explanation']}")
        
        if concept.get("core_signals"):
            text_parts.append(f"\n\nCore signals:\n{', '.join(concept['core_signals'])}")
        
        if concept.get("advanced_signals"):
            text_parts.append(f"\n\nAdvanced signals:\n{', '.join(concept['advanced_signals'])}")
        
        if concept.get("common_misconceptions"):
            text_parts.append(f"\n\nCommon misconceptions:\n{', '.join(concept['common_misconceptions'])}")
        
        text = "".join(text_parts)
        
        # Create chunk
        chunk = {
            "id": chunk_id,
            "text": text,
            "metadata": {
                "concept": concept_name,
                "domain": domain,
                "subdomain": subdomain,
                "level": level,
                "difficulty": level
            }
        }
        
        chunks.append(chunk)
    
    # Report missing mappings
    if missing_domains:
        print("\n⚠️  Missing domain mappings for:")
        for concept in sorted(missing_domains)[:10]:
            print(f"  - {concept}")
        if len(missing_domains) > 10:
            print(f"  ... and {len(missing_domains) - 10} more")
    
    if missing_levels:
        print("\n⚠️  Missing level mappings for:")
        for mapping in sorted(missing_levels)[:10]:
            print(f"  - {mapping}")
        if len(missing_levels) > 10:
            print(f"  ... and {len(missing_levels) - 10} more")
    
    return chunks

# ==========================
# LOAD AND PROCESS DATA
# ==========================

# Load concepts
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    concepts = json.load(f)

print(f"Loaded {len(concepts)} concepts")

# Create chunks
chunks = create_chunks(concepts)

# ==========================
# PRINT STATISTICS
# ==========================

print("\n" + "=" * 60)
print("LEVEL CLASSIFICATION RESULTS")
print("=" * 60)

# Level distribution
level_counts = Counter(chunk["metadata"]["level"] for chunk in chunks)
print("\nOverall level distribution:")
for level in ["L1", "L2", "L3"]:
    count = level_counts.get(level, 0)
    percentage = (count / len(chunks)) * 100
    print(f"  {level}: {count} chunks ({percentage:.1f}%)")

# Domain distribution
domain_counts = {}
for chunk in chunks:
    domain = chunk["metadata"]["domain"]
    level = chunk["metadata"]["level"]
    
    if domain not in domain_counts:
        domain_counts[domain] = {"L1": 0, "L2": 0, "L3": 0, "total": 0}
    
    domain_counts[domain][level] += 1
    domain_counts[domain]["total"] += 1

print("\nDistribution by domain:")
for domain, stats in sorted(domain_counts.items()):
    if domain == "unknown":
        continue
    print(f"\n{domain}:")
    for level in ["L1", "L2", "L3"]:
        count = stats[level]
        if count > 0:
            percentage = (count / stats["total"]) * 100
            print(f"  {level}: {count} ({percentage:.1f}%)")

# ==========================
# SAVE CHUNKS
# ==========================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=2, ensure_ascii=False)

print(f"\n✅ Created {len(chunks)} chunks")
print(f"✅ Saved to: {OUTPUT_FILE}")

# ==========================
# SHOW SAMPLE
# ==========================

print("\n" + "=" * 60)
print("SAMPLE CLASSIFICATIONS")
print("=" * 60)

# Group by level for sample
samples_by_level = {"L1": [], "L2": [], "L3": []}
for chunk in chunks:
    level = chunk["metadata"]["level"]
    if len(samples_by_level[level]) < 3:  # Show 3 per level
        samples_by_level[level].append(chunk)

for level in ["L1", "L2", "L3"]:
    print(f"\n{level} EXAMPLES:")
    for chunk in samples_by_level[level]:
        print(f"  • {chunk['metadata']['concept']}")
        print(f"    ({chunk['metadata']['domain']} / {chunk['metadata']['subdomain']})")

# ==========================
# EXPORT TO CSV FOR ANALYSIS
# ==========================

def export_to_csv():
    """Export the chunks to CSV for easier analysis"""
    import csv
    
    csv_file = "chunks_analysis.csv"
    
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Concept", "Domain", "Subdomain", "Level", "Text Length"])
        
        for chunk in chunks:
            writer.writerow([
                chunk["id"],
                chunk["metadata"]["concept"],
                chunk["metadata"]["domain"],
                chunk["metadata"]["subdomain"],
                chunk["metadata"]["level"],
                len(chunk["text"])
            ])
    
    print(f"\n📊 Analysis exported to: {csv_file}")

# Uncomment to export CSV
# export_to_csv()