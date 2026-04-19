from app.agents.planner_agent import PlannerAgent
from app.validators.source_validator import SourceValidator


def test_planner_returns_distinct_facets():
    planner = PlannerAgent()
    queries = planner.plan_queries("state of ai agents")

    assert queries[0] == "state of ai agents"
    assert len(queries) == len(set(queries))
    assert any("risks" in query for query in queries)


def test_validator_prefers_trusted_domains():
    validator = SourceValidator()
    trusted = validator.score("https://www.nasa.gov/article", "content" * 700)
    untrusted = validator.score("https://example-blog.xyz/post", "content" * 700)

    assert trusted > untrusted
