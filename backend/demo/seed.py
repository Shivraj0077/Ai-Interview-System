"""
Sample interviews so the dashboard is populated on first launch.

These are clearly flagged `is_sample` and are read-only in the UI. They use
real concepts and signals from the knowledge base, and their evaluations go
through the same grounding verification, evidence cap and report builder as
live interviews, so the sample reports look exactly like real ones.
"""

import uuid
from datetime import datetime, timedelta, timezone

from interview.difficulty import update_difficulty
from interview.evaluator import apply_evidence_cap, normalize, verify_grounding
from interview.report import build_report
from rag.retrieval import concept_name

# (concept id prefix, question, answer, covered core idx, covered advanced idx, misconception idx, score, communication)
SAMPLES = [
    {
        "candidate_name": "Priya Sharma",
        "role": "Backend Engineer Intern",
        "focus_areas": ["backend", "database", "distributed_systems"],
        "num_questions": 6,
        "days_ago": 2,
        "turns": [
            ("concept_0032", "Walk me through what happens between a user hitting 'Pay' in the browser and your API handler starting to run.",
             "The browser resolves the domain with a DNS lookup, then opens a TCP connection and does the TLS handshake. The request goes out with headers like auth and content-type plus a JSON body, usually through a load balancer, and only then does our server-side code parse and handle it. Each of those steps adds round trips, which is why latency isn't just our code.",
             [0, 1, 2, 3, 4], [0], [], 9, 9),
            ("concept_0048", "Our orders table has grown to a few million rows and filtering by customer_id is slow. How would you think about adding an index?",
             "I'd add a B-tree index on customer_id so the query can seek instead of doing a full table scan on the WHERE filter. The trade-off is extra storage and a write tax on every insert and update, so I wouldn't index every column. If we also sort by created_at, a composite index on (customer_id, created_at) could cover it.",
             [0, 1, 2, 3, 4, 5], [2], [], 8, 8),
            ("concept_0120", "If our payment service consumes events from a queue, what delivery guarantee would you expect, and what does that mean for how you write the consumer?",
             "Most brokers give at-least-once, so the consumer only ACKs after processing and a message can be redelivered. That means duplicates can happen, so charging a card twice is possible unless we handle it. I'd store processed message IDs.",
             [0, 1, 2], [], [], 5, 7),
            ("concept_0117", "A downstream fraud-check API is flaky. How would you design retries for calls to it?",
             "Only retry transient failures like timeouts or 503s, not 400s. Use exponential backoff with a random jitter so thousands of clients don't retry at the same moment and cause a thundering herd, and cap the number of attempts so we don't exhaust resources. The call also has to be idempotent so a retry doesn't double-apply.",
             [0, 1, 2, 3, 4], [0, 1], [], 8, 9),
            ("concept_0122", "When an order is saved we also need to publish an OrderCreated event. How do you make sure the database write and the event never disagree?",
             "Writing to the DB and then publishing is a dual-write problem, one can fail. I'd write the event into an outbox table in the same transaction and have a relay publish it afterwards, so it's eventually consistent.",
             [0, 1, 4, 5], [], [], 6, 7),
            ("concept_0119", "Some events keep failing no matter how many times the consumer retries. What would you do with them?",
             "I'd send them to a dead letter queue immediately when they fail so they don't block the main queue.",
             [0, 1], [], [0], 4, 6),
        ],
    },
    {
        "candidate_name": "Daniel Okafor",
        "role": "Software Engineer",
        "focus_areas": ["programming_fundamentals", "backend"],
        "num_questions": 5,
        "days_ago": 5,
        "turns": [
            ("concept_0005", "Can you explain what a closure is, maybe with an example of where you'd actually use one?",
             "A closure is an inner function that keeps access to variables from its lexical scope even after the outer function returns. I've used it for a counter factory where the count is private, so it gives you data privacy and state preservation.",
             [0, 1, 2, 3], [0], [], 7, 8),
            ("concept_0029", "When designing an endpoint to update a user's profile, how do you choose between PUT, POST and PATCH?",
             "PUT replaces the resource and is idempotent, PATCH is a partial update, POST creates or triggers actions and isn't idempotent. GET should be safe with no side effects. I map them to CRUD and keep the data in the request body, not query params.",
             [0, 1, 2, 3, 4, 6], [0], [], 8, 8),
            ("concept_0013", "How does async/await relate to promises, and what happens to the rest of the program while an await is pending?",
             "Async/await makes code look synchronous. When you await, the whole program waits until the promise resolves, so you should avoid it in hot paths.",
             [0, 4], [], [0], 4, 6),
            ("concept_0010", "How do you approach error handling in a service so failures don't take the whole request down?",
             "Wrap risky operations in try-catch at the right scope, log the error with context, and fail gracefully instead of crashing. I use finally to release resources like DB connections and throw custom error types so callers can tell validation errors from real failures. Exceptions should propagate to a central handler rather than being swallowed.",
             [0, 1, 2, 3, 4, 6], [2], [], 8, 9),
            ("concept_0091", "Why do people say APIs should be stateless, and where does session data go then?",
             "Stateless means each request carries everything needed, like a JWT, so any server can handle it. That makes horizontal scaling easy behind a load balancer. Session state moves to a shared store.",
             [0, 2, 3, 4], [], [], 6, 7),
        ],
    },
    {
        "candidate_name": "Mei Lin",
        "role": "DevOps Engineer Intern",
        "focus_areas": ["devops", "observability"],
        "num_questions": 4,
        "days_ago": 9,
        "turns": [
            ("concept_0067", "What problem do containers solve for a team shipping a web service?",
             "Docker packages the app with its dependencies into an image so it runs the same everywhere. It's basically a lightweight virtual machine.",
             [0, 1, 6], [], [0], 5, 6),
            ("concept_0068", "Describe what a good CI/CD pipeline does on every pull request and every merge.",
             "On every PR the pipeline builds the code and runs automated tests, so bugs are caught early and developers get fast feedback. On merge to main it builds the artifact and automates deployment. We used GitHub Actions for this, and I'd add a rollback step for bad releases.",
             [0, 1, 2, 3, 4, 6], [1], [], 8, 8),
            ("concept_0070", "How would you decide what to monitor and alert on for a production API?",
             "I'd look at the logs when something breaks and set up alerts for CPU.",
             [0], [], [], 3, 5),
            ("concept_0109", "What does a GitHub Actions workflow file contain?",
             "It's a YAML file with triggers like push or pull request, and jobs that contain steps for building and testing.",
             [2, 3, 4, 5], [], [], 6, 6),
        ],
    },
    {
        "candidate_name": "Alex Rivera",
        "role": "Full-Stack Engineer",
        "focus_areas": ["backend", "security", "programming_fundamentals"],
        "num_questions": 6,
        "days_ago": 0,
        "status": "in_progress",
        "turns": [
            ("concept_0030", "A client calls your API with an expired token, and another calls with a valid token but asks for someone else's data. What status codes do you return and why?",
             "Expired token is 401 because they're not authenticated, the second is 403 because they're authenticated but not permitted. 4xx means the client did something wrong, 5xx is on us, and I'd never return 200 with an error inside the body.",
             [0, 1, 2, 3], [2], [], 8, 9),
            ("concept_0090", "Your React app on app.example.com gets a CORS error calling api.example.com. What's going on and how do you fix it?",
             "Browsers enforce the same-origin policy, so the API has to send Access-Control-Allow-Origin headers for the app's origin. For non-simple requests the browser sends a preflight OPTIONS request first. It's fixed on the server by allowing the origin, not in the frontend.",
             [0, 1, 2, 4, 5], [], [], 7, 8),
            ("concept_0037", "Your team uses JWTs for auth. What's inside a JWT, and what should or shouldn't go in it?", None, [], [], [], 0, 0),
        ],
    },
]


def _evaluation(concept, core_idx, adv_idx, misc_idx, score, comm):
    raw = {
        "score": score,
        "communication_score": comm,
        "core_coverage": [concept["core_signals"][i] for i in core_idx],
        "advanced_coverage": [concept["advanced_signals"][i] for i in adv_idx],
        "missed_core_signals": [],
        "misconceptions_detected": [concept["misconceptions"][i] for i in misc_idx],
    }
    ev = verify_grounding(normalize(raw), concept["core_signals"], concept["advanced_signals"], concept["misconceptions"])
    return apply_evidence_cap(ev, concept["core_signals"])


def build_samples(catalog: dict[str, dict], engine_info: dict) -> list[dict]:
    by_prefix = {cid[:12]: c for cid, c in catalog.items()}
    samples = []
    for spec in SAMPLES:
        created = datetime.now(timezone.utc) - timedelta(days=spec["days_ago"], hours=3)
        difficulty = "L1"
        turns = []
        for i, (prefix, question, answer, core, adv, misc, score, comm) in enumerate(spec["turns"]):
            concept = by_prefix[prefix]
            asked = created + timedelta(minutes=2 + 3 * i)
            turn = {
                "index": i,
                "concept_id": concept["id"],
                "concept_name": concept_name(concept),
                "domain": concept["domain"],
                "subdomain": concept.get("subdomain"),
                "difficulty": concept["difficulty"],
                "target_difficulty": difficulty,
                "advanced_signal_count": len(concept["advanced_signals"]),
                "question": question,
                "answer": answer,
                "evaluation": None,
                "skipped": False,
                "retrieval_mode": "semantic",
                "retrieval_note": None,
                "asked_at": asked.isoformat(),
                "answered_at": None,
            }
            if answer is not None:
                turn["evaluation"] = _evaluation(concept, core, adv, misc, score, comm)
                turn["answered_at"] = (asked + timedelta(minutes=2)).isoformat()
                difficulty = update_difficulty(difficulty, turn["evaluation"]["score"])
            turns.append(turn)

        status = spec.get("status", "completed")
        interview = {
            "id": "sample-" + uuid.uuid4().hex[:8],
            "created_at": created.isoformat(),
            "updated_at": (created + timedelta(minutes=3 * len(turns) + 2)).isoformat(),
            "status": status,
            "is_sample": True,
            "candidate_name": spec["candidate_name"],
            "role": spec["role"],
            "config": {
                "interview_type": "technical",
                "difficulty_mode": "adaptive",
                "start_difficulty": "L1",
                "num_questions": spec["num_questions"],
                "focus_areas": spec["focus_areas"],
                "job_description": "",
                "resume_text": "",
                "resume_filename": None,
            },
            "state": {
                "current_difficulty": difficulty,
                "used_concepts": [t["concept_id"] for t in turns],
                "turns": turns,
                "started_at": created.isoformat(),
                "finished_at": None,
                "engine": engine_info,
            },
            "report": None,
        }
        if status == "completed":
            interview["state"]["finished_at"] = interview["updated_at"]
            interview["report"] = build_report(interview)
        samples.append(interview)
    return samples


def ensure_samples(engine) -> None:
    """Insert the sample interviews once (when none exist yet)."""
    if engine.repo.count_samples() > 0:
        return
    for sample in build_samples(engine.retriever.catalog, engine.engine_info):
        engine.repo.save(sample)
