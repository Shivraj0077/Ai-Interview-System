import json
import re
import hashlib
from collections import Counter

INPUT_FILE = "Rag-db.json"  # Your input file with the concepts
OUTPUT_FILE = "final-chunks.json"

# ==========================
# DOMAIN/SUBDOMAIN MAPPING
# ==========================
# You'll need to define domain/subdomain for each concept
# This is a starting point - you should adjust based on your concepts

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
# LEVEL CLASSIFICATION KEYWORDS
# ==========================

L1_KEYWORDS = [
    "basic", "fundamental", "simple", "introduction", "basics", "core",
    "syntax", "beginner", "overview", "definition", "what is", "concept",
    "primitive", "control flow", "variables", "functions", "scope",
    "arrays", "strings", "loops", "conditionals", "fresher", "junior",
    "blueprint", "instance", "visibility", "lifetime", "reusable"
]

L2_KEYWORDS = [
    "optimization", "performance", "design pattern", "architecture",
    "security", "authentication", "authorization", "middleware",
    "caching", "indexing", "normalization", "api design", "restful",
    "microservices", "docker", "ci/cd", "testing", "refactoring",
    "technical debt", "code quality", "error handling", "concurrency",
    "async", "promises", "callback", "event loop", "middleware",
    "scalability", "load balancing", "replication", "versioning",
    "trade-offs", "optimize", "bottleneck", "profiling", "monitoring"
]

L3_KEYWORDS = [
    "distributed", "high availability", "fault tolerance",
    "consistency", "sharding", "partitioning", "event sourcing",
    "cqrs", "saga", "circuit breaker", "bulkhead", "message queue",
    "kafka", "rabbitmq", "kubernetes", "orchestration", "service mesh",
    "observability", "opentelemetry", "tracing", "auto-scaling",
    "chaos engineering", "eventual consistency", "cap theorem",
    "idempotency", "exponential backoff", "jitter", "dead letter",
    "correlation id", "structured logging", "span", "trace"
]

# ==========================
# LEVEL DETECTION FUNCTION
# ==========================

def detect_level(concept_data):
    """
    Detect the appropriate level (L1, L2, L3) for a concept
    Uses multiple signals: explanation content, signals, and misconceptions
    """
    # Combine all text for analysis
    text = (
        concept_data["explanation"] + " " +
        " ".join(concept_data.get("core_signals", [])) + " " +
        " ".join(concept_data.get("advanced_signals", [])) + " " +
        " ".join(concept_data.get("common_misconceptions", []))
    ).lower()
    
    # Count keyword matches for each level
    l1_count = sum(1 for kw in L1_KEYWORDS if kw in text)
    l2_count = sum(1 for kw in L2_KEYWORDS if kw in text)
    l3_count = sum(1 for kw in L3_KEYWORDS if kw in text)
    
    # Advanced signals boost
    if concept_data.get("advanced_signals"):
        # If there are advanced signals, boost L2/L3
        if any("distributed" in s.lower() or "cluster" in s.lower() or "scale" in s.lower() 
               for s in concept_data["advanced_signals"]):
            l3_count += 2
        else:
            l2_count += 2
    
    # Core signals analysis
    core_text = " ".join(concept_data.get("core_signals", [])).lower()
    if any(kw in core_text for kw in ["complexity", "performance", "optimization", "design", "pattern"]):
        l2_count += 1
    if any(kw in core_text for kw in ["distributed", "consistency", "fault", "tolerance"]):
        l3_count += 2
    
    # Weighted scoring
    total_keywords = l1_count + l2_count + l3_count
    if total_keywords == 0:
        return "L1"  # Default to L1 if no keywords found
    
    # Calculate weighted score (L1=1, L2=2, L3=3)
    weighted_score = (l1_count * 1 + l2_count * 2 + l3_count * 3) / total_keywords
    
    # Determine level based on weighted score
    if weighted_score < 1.5:
        return "L1"
    elif weighted_score < 2.3:
        return "L2"
    else:
        return "L3"

# ==========================
# CREATE CHUNKS
# ==========================

def create_chunks(concepts):
    """Convert concepts to chunks with metadata"""
    chunks = []
    
    for i, concept in enumerate(concepts):
        concept_name = concept["concept"]
        
        # Get domain and subdomain from mapping
        domain_info = DOMAIN_MAPPING.get(concept_name, ("unknown", "unknown"))
        domain, subdomain = domain_info
        
        # Detect level
        level = detect_level(concept)
        
        # Create ID
        # Convert concept name to a valid ID format
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
                "level": level,  # This is the level we detect
                "difficulty": level  # Set difficulty same as level initially
            }
        }
        
        chunks.append(chunk)
    
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
# OPTIONAL: SHOW SAMPLE
# ==========================

print("\n" + "=" * 60)
print("SAMPLE CLASSIFICATIONS")
print("=" * 60)

# Show first 10 chunks as examples
for i, chunk in enumerate(chunks[:10]):
    print(f"\n{i+1}. {chunk['metadata']['concept']}")
    print(f"   Domain: {chunk['metadata']['domain']} / {chunk['metadata']['subdomain']}")
    print(f"   Level: {chunk['metadata']['level']}")
    print(f"   Preview: {chunk['text'][:100]}...")

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