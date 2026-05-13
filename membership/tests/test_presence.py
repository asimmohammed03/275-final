from membership.presence import PresenceManager, PresenceState


def test_register_member():
    events = []
    pm = PresenceManager(lambda u, c: events.append((u, c)))

    pm.register_member("alice")

    entry = pm.get_member_presence("alice")
    assert entry.state == PresenceState.ALIVE


def test_heartbeat_updates():
    pm = PresenceManager(lambda u, c: None)

    pm.register_member("alice")
    before = pm.get_member_presence("alice").last_heartbeat

    pm.record_heartbeat("alice")
    after = pm.get_member_presence("alice").last_heartbeat

    assert after >= before


def test_suspected_state():
    events = []

    fake_time = [0]

    def time_fn():
        return fake_time[0]

    def callback(u, c):
        events.append((u, c))

    pm = PresenceManager(callback, time_fn=time_fn)

    pm.register_member("alice")

    fake_time[0] += 20  # simulate time passing
    pm.check_liveness()

    assert events[0][1] == "suspected"


def test_reconnected():
    events = []
    fake_time = [0]

    def time_fn():
        return fake_time[0]

    def callback(u, c):
        events.append((u, c))

    pm = PresenceManager(callback, time_fn=time_fn)

    pm.register_member("alice")

    fake_time[0] += 20
    pm.check_liveness()

    pm.record_heartbeat("alice")

    assert events[-1][1] == "reconnected"


def test_timeout():
    events = []
    fake_time = [0]

    def time_fn():
        return fake_time[0]

    def callback(u, c):
        events.append((u, c))

    pm = PresenceManager(callback, time_fn=time_fn)

    pm.register_member("alice")

    fake_time[0] += 20
    pm.check_liveness()

    fake_time[0] += 20
    pm.check_liveness()

    assert events[-1][1] == "timeout"
