# 5gcsdk — OAI 5G Core Northbound SDK

`5gcsdk` is a Python toolkit for **observing and controlling an OAI 5G Core
from the outside**, over its standard 3GPP northbound service-based interfaces.

The OAI network functions already expose 3GPP-compliant *event exposure* services — `Namf_EventExposure`
on the AMF, `Nsmf_EventExposure` on the SMF, and optionally `Nnwdaf_EventsSubscription` on NWDAF. What they
do not provide is a consumer. This SDK is that consumer: it subscribes on your behalf, receives the
resulting notification callbacks, normalises them into a queryable store, and hands you a small Python API
plus a user-callback mechanism on top.

In other words, it plays the role that an application function (AF), an OSS, or an external analytics
platform would play against a real operator core — but small enough to drive from a script or a test suite.

It is used in two ways:

- **As a lab/teaching SDK** — attach to a running core, ask "which UEs are registered?", "what is this
  IMSI's status?", "how much traffic did this subscriber use?", and run your own code whenever a UE
  registers, changes state, or reports traffic usage.
- **As a test oracle** — the `Northbound.robot` suite in
  [`oai-cn5g-fed`](https://github.com/openairinterface/oai-cn5g-fed) drives this SDK to assert that the AMF
  and SMF actually emit correct notifications during registration, PDU session establishment,
  deregistration, and inter-gNB handover.

---

## How it works

```
                    ┌──────────────────────────────────────────┐
                    │              OAI 5G Core                 │
                    │                                          │
   ① subscribe ────►│  AMF   /namf-evts/v1/subscriptions       │
   (HTTP POST)      │  SMF   /nsmf-event-exposure/v1/subs...   │
                    │  NWDAF /nnwdaf-eventssubscription/v1     │
                    └───────────────────┬──────────────────────┘
                                        │
                                        │ ② notify (HTTP POST to eventNotifyUri)
                                        ▼
                    ┌──────────────────────────────────────────┐
                    │        handler.py  (Flask, :1112)        │
                    │                                          │
                    │  /callbacks/amf-reports                  │
                    │  /callbacks/dataplane-reports            │
                    │  /notification                           │
                    │  /anomaly_notification                   │
                    │  /network_performance_notification       │
                    └───────┬──────────────────────────┬───────┘
                            │ ③ persist                │ ④ dispatch
                            ▼                          ▼
                ┌───────────────────────┐   ┌───────────────────────┐
                │ MongoDB               │   │ your callbacks        │
                │ db: notification_db   │   │ (callbacks.py +       │
                │                       │   │  events.json)         │
                └───────────┬───────────┘   └───────────────────────┘
                            │ ⑤ query
                            ▼
                ┌───────────────────────────────────────────────┐
                │  UEManager · NFManager · RFsimUEManager ·      │
                │  CallbackManager · datamanager                │
                └───────────────────────────────────────────────┘
```

1. **Subscribe.** On startup, `handler.py` calls into `src/subscriptions_manager/subscriptions.py` to create
   event-exposure subscriptions, passing its own address as the `eventNotifyUri` / `notifUri`. By default it
   registers for AMF `REGISTRATION_STATE_REPORT` and `LOCATION_REPORT`, and SMF `PDU_SES_EST` and `QOS_MON`.
   It also attempts three NWDAF subscriptions (network performance, abnormal behaviour, UE mobility); these are
   best-effort, and the handler starts even if the NWDAF is absent.
2. **Receive.** The core POSTs notifications back to the Flask endpoints as events occur.
3. **Persist.** Each AMF and SMF notification is written to a MongoDB collection, split by kind:

   | Collection | Contents |
   |---|---|
   | `amf_notifications` | registration state reports |
   | `amf_location_notification` | `LOCATION_REPORT` events (cell ID, TAI) |
   | `smf_notifications` | PDU session establishment (SUPI, DNN, allocated IPv4, session ID) |
   | `smf_notification_traffic` | `QOS_MON` usage reports (uplink/downlink volumes) |

   NWDAF notifications are only logged, not stored.

4. **Dispatch.** If you have registered any callbacks, the matching ones are invoked with the freshly
   received data.
5. **Query.** The modules under `src/modules/` read back from MongoDB and present the data as Python objects.

Because everything lands in MongoDB first, the query API and your callbacks see a consistent view. Note that the
handler empties these collections when it starts, so history does not survive a handler restart.

---

## Repository layout

```
etc/
  configuration.yaml      # where the AMF/SMF/NWDAF live, and where the handler binds
  handler_status.yaml     # runtime state: is the handler running, and under which PID
src/
  main/
    handler.py            # the Flask notification sink — the heart of the SDK
    init_handler.py       # start_handler() / stop_handler() lifecycle helpers
    oai5gc.py             # top-level convenience import that re-exports the modules
  subscriptions_manager/
    subscriptions.py      # builds and POSTs the 3GPP subscription bodies
  modules/
    UEManager.py          # get_registered_ues(), get_ue_status(), get_ue_traffic()
    RFsimUEManager.py     # add_ues() / remove_ues() / list_connected_ues() via docker compose
    CallbackManager.py    # register_callback_ue() / unregister_callback_ue()
    NFManager.py          # register_nf() — subscribe to an NF by IP at runtime
    datamanager.py        # export a filtered view of collected metrics to CSV
    callbacks.py          # GENERATED — holds the source of your registered callbacks
    events.json           # GENERATED — maps event types to registered callback names
    data_models/          # UE, Metric, EventType, UEStatus, TrafficVolume, DataStream
tests/
  test.py                 # scratch usage examples
docs/                     # pre-built Doxygen output (html + latex)
```

---

## Configuration

Everything the SDK needs to reach the core is in `etc/configuration.yaml`:

```yaml
amf_1:
  url: /namf-evts/v1        # event exposure base path
  ip: 192.168.79.132        # must match the AMF's SBI address
  port: 8080
smf_1:
  url: /nsmf-event-exposure/v1
  ip: 192.168.79.133
  port: 8080
sbi:
  ip: 192.168.79.129        # address the handler BINDS to — must exist on this host
  port: 1112                # and be reachable from the core's containers
```

`sbi.port` is only advertised to the core in the notification URIs; the handler always listens on port 1112
(hardcoded in `app.run()`), so leave it at `1112`.

`sbi.ip` is the one people get wrong. It is not a target — it is the local address Flask binds to, and it is
also what gets advertised to the core as the notification URI. It therefore has to be an address that exists
on the machine running the handler *and* is routable from inside the NF containers. On a Docker Compose
deployment that is normally the gateway address of the bridge the core sits on.

---

## Lifecycle

`init_handler.py` runs the handler as a separate child process and tracks it in `etc/handler_status.yaml`.
These modules are not installable packages, so put `src/main` on the import path first:

```python
import sys
sys.path.append("src/main")   # relative to the SDK checkout; use an absolute path elsewhere

from init_handler import start_handler, stop_handler, check_handler_ready

start_handler()        # spawns handler.py, records its PID, marks status 'on'
check_handler_ready()  # raises AssertionError if the handler is not up and serving yet
...
stop_handler()    # clears registered callbacks, terminates the handler, marks status 'off'
```

`stop_handler()` does **not** delete the AMF/SMF/NWDAF subscriptions. `handler.py` defines a SIGTERM handler
for that, but registers it only after `app.run()`, which never returns, so it is never installed. The
subscriptions stay on the core until the NFs are restarted.

`start_handler()` checks the recorded PID rather than trusting the status flag. If the file says `'on'` but
that process is gone (a crash, a `kill -9`), it logs a warning and starts a new handler. If a handler really is
running, it raises `RuntimeError`. `stop_handler()` always resets the status file, even if the handler had
already died.

Use `check_handler_ready()` after `start_handler()` to fail fast: it raises `AssertionError` unless the
handler process is alive and accepting connections on `sbi.ip:sbi.port`. It checks once, and the handler
needs a moment to connect to MongoDB and subscribe, so retry it for a few seconds rather than calling it once
(`Northbound.robot` retries for up to 30 s). Since the handler creates its
subscriptions before it starts serving, and exits if they fail, an open port means the subscriptions were
accepted.

MongoDB must be reachable at `mongodb://localhost:27017/` before the handler starts; it exits immediately
otherwise.

---

## Using it

```python
import sys
sys.path.append("src/main")        # see Lifecycle above

import oai5gc                      # importing this also calls start_handler()
from data_models.EventType import EventType
from data_models.TrafficVolume import TrafficVolume

# --- query -------------------------------------------------------------
for ue in oai5gc.UEManager.get_registered_ues():
    print(ue.supi, ue.ad_ipv4_addr, ue.rm_state)

oai5gc.UEManager.get_ue_status("imsi-208950000000031")   # -> UEStatus.REGISTERED
oai5gc.UEManager.get_ue_status("12.1.1.130")             # lookup by allocated IP also works

usage = oai5gc.UEManager.get_ue_traffic("2026-08-07 12:00:00", "2026-08-07 13:00:00")
print(usage[TrafficVolume.TOTAL_UPLINK], usage[TrafficVolume.TOTAL_DOWNLINK])

# --- react -------------------------------------------------------------
def on_new_ue(data):
    print("UE registered:", data)

oai5gc.register_callback_ue(on_new_ue, EventType.REGISTERED_UES)

# --- drive the RAN (rfsim deployments) ---------------------------------
oai5gc.RFsimUEManager.add_ues(3)
oai5gc.RFsimUEManager.list_connected_ues()
```

Callback registration is worth understanding before you rely on it: `register_callback_ue()` uses
`inspect.getsource()` to extract your function's **source text** and appends it to `src/modules/callbacks.py`,
recording the name in `events.json`. The handler then `importlib.reload()`s that module and looks the function
up by name. This makes callbacks survive across processes — the handler runs separately from your script — but
it also means your callback must be self-contained: closures, decorators, and references to names from your
own module will not resolve inside `callbacks.py`. Both files are generated; do not hand-edit them.

Available event types are `EventType.REGISTERED_UES`, `UE_STATUS` and `UE_TRAFFIC`. `UE_CELL_ID` can be
registered but is not dispatched by the handler yet, so those callbacks never fire.

---

## Role in the oai-cn5g-fed CI

The federation repository does not vendor this SDK. `ci-scripts/Jenkinsfile-RobotTests` clones it into
`test/5gcsdk` at build time and `test/Northbound.robot` loads `src/main/init_handler.py` as a Robot Framework
library:

```robotframework
Library    5gcsdk/src/main/init_handler.py    WITH NAME    Handler
...
Handler.Start Handler
```

The suite then brings up a core plus an rfsim RAN, lets UEs attach, and asserts that what the SDK collected in
MongoDB matches what the AMF and SMF logs say happened.

### Pointing the SDK at your core

The defaults in `etc/configuration.yaml` target the robot test bed (`192.168.79.x`). Against any other
deployment — for example the tutorial deployment on `192.168.70.x` — set `amf_1.ip`, `smf_1.ip` and `sbi.ip` to
match it, otherwise the handler cannot bind and the AMF and SMF are unreachable.

The SDK speaks HTTP/1.1 only: subscriptions are sent with `requests`, and the handler *serves* on Flask's
built-in development server. The core must therefore be configured with `http_version: 1`. Serving HTTP/2 would
require replacing `app.run()` with an HTTP/2-capable server.

---

## Requirements

Python 3.10+, a reachable MongoDB, and:

```
Flask  pymongo  requests  PyYAML  psutil  docker
```

`RFsimUEManager` additionally needs Docker access, the standalone `docker-compose` command (it does not use
`docker compose`), and an rfsim compose file at
`template/northbound_templates/docker-compose-northbound.yaml`, resolved relative to the SDK checkout's parent
directory (i.e. `test/template/northbound_templates/` when the SDK sits in `oai-cn5g-fed/test/5gcsdk`).

---

## Further reading

Pre-built API documentation is in `docs/html/index.html` (Doxygen). Module docstrings are the authoritative
reference for arguments and return types.
