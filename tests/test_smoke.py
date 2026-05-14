from ctx_proxy.session import Session


def test_session_utilization():
    session = Session(
        session_id="session-1",
        provider="openai",
        model="gpt-4o",
        token_limit=100,
    )

    assert session.utilization() == 0.0
